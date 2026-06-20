"""
Agent Orchestrator — coordinates the four-stage AI coaching pipeline.

Runs agents sequentially: AnalystAgent → PlannerAgent → CoachAgent.
Analyst and Planner outputs are cached for 24 hours per user and
invalidated automatically when the user logs a new activity.
The CoachAgent always runs fresh (never cached) to ensure coaching
remains timely and relevant.
"""

import logging
import json
from typing import AsyncGenerator

logger = logging.getLogger(__name__)
from app.db.database import get_user_context
from app.agents.baseline_agent import BaselineAgent
from app.agents.analyst_agent import AnalystAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.coach_agent import CoachAgent
from app.services.insights_cache import insights_cache
from app.models.schemas import AnalysisResult, PlanResult, GeminiError

import datetime

class AgentOrchestrator:
    """
    Lightweight sequential pipeline orchestrator.

    Instantiated once at module level as a singleton and reused across
    all incoming requests. Each agent receives only the typed Pydantic
    output of the previous stage — no raw strings pass between agents.
    """
    def __init__(self):
        self.baseline_agent = BaselineAgent()
        self.analyst_agent = AnalystAgent()
        self.planner_agent = PlannerAgent()
        self.coach_agent = CoachAgent()
        self.cache = insights_cache

    async def run_pipeline(self, user_id: str) -> AsyncGenerator[str, None]:
        """
        Execute the Analyst → Planner → Coach pipeline for a user.

        Serves cached Analyst and Planner results when available (24-hour TTL,
        invalidated on new activity log). Always runs the Coach stage fresh.

        Args:
            user_id: The UUID of the user to analyse.

        Yields:
            str: Status tokens and Coach Agent response tokens for SSE.
                 Final token is always "[PIPELINE_COMPLETE]".
                 Error token format: "[ERROR] <user-safe message>".
        """
        try:
            yield f"🔄 **[System]** Initiating Full AI Analysis for User {user_id[:8]}...\n"
            yield "[NEXT_MESSAGE]"
            context = await get_user_context(user_id)
            
            yield "📊 **[Analyst Agent]** Reading carbon footprint history and baseline data...\n"
            
            # Analyst Cache check
            analyst_json = await self.cache.get(user_id, "analyst")
            if analyst_json:
                yield "⚡ **[Analyst Agent]** Analysis retrieved from cache.\n"
                analysis = AnalysisResult.model_validate_json(analyst_json)
            else:
                yield "🧠 **[Analyst Agent]** Identifying primary carbon hotspots and patterns...\n"
                analysis = await self.analyst_agent.analyze(context)
                await self.cache.set(user_id, "analyst", analysis.model_dump_json())
                yield f"✅ **[Analyst Agent]** Analysis complete. Primary hotspot identified: **{analysis.primary_hotspot}**.\n"
                
            yield "[NEXT_MESSAGE]"

            yield "🗺️ **[Planner Agent]** Generating actionable reduction strategies and missions...\n"
            # Planner Cache check
            planner_json = await self.cache.get(user_id, "planner")
            if planner_json:
                yield "⚡ **[Planner Agent]** Plan retrieved from cache.\n"
                plan = PlanResult.model_validate_json(planner_json)
            else:
                plan = await self.planner_agent.plan(context, analysis)
                await self.cache.set(user_id, "planner", plan.model_dump_json())
                yield f"✅ **[Planner Agent]** Plan complete. Generated **{len(plan.strategies)}** tailored strategies.\n"
                
            yield "[NEXT_MESSAGE]"

            yield "💾 **[System Orchestrator]** Syncing new strategies to Mission Center database...\n"
            await self._auto_generate_missions(user_id, plan)
            yield "✅ **[System Orchestrator]** Missions synced successfully. Check your Mission Center!\n"
            
            yield "[NEXT_MESSAGE]"

            yield "💬 **[Coach Agent]** Synthesizing final report...\n\n---\n\n"
            
            # Coach stream
            async for token in self.coach_agent.coach_stream(context, analysis, plan):
                yield token

            yield "[UPDATE_DASHBOARD]"
                
        except GeminiError:
            yield "[ERROR] Analysis temporarily unavailable."
        except Exception:
            logger.exception("Pipeline execution failed for user_id prefix %s", user_id[:8])
            yield "[ERROR] An unexpected error occurred. Please try again."

    async def _auto_generate_missions(self, user_id: str, plan: PlanResult):
        """
        Persist mission rows from the Planner's strategies to the database.

        Skips strategies that already have an existing mission with the same
        title to prevent duplicate missions on repeated pipeline runs.

        Args:
            user_id: Target user UUID.
            plan:    PlanResult from PlannerAgent containing strategies.
        """
        from app.db.database import get_db_context
        async with get_db_context() as db:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for s in plan.strategies:
                if s.mission_type:
                    async with db.execute("SELECT id FROM missions WHERE user_id = ? AND title = ?", (user_id, s.title)) as cursor:
                        exists = await cursor.fetchone()
                    if exists:
                        continue
                    
                    difficulty = s.difficulty.lower().strip()
                    reward = 100
                    if difficulty == "medium":
                        reward = 200
                    elif difficulty == "hard":
                        reward = 300
                        
                    await db.execute(
                        """
                        INSERT INTO missions (user_id, title, description, category, target_reduction_kg, eco_points_reward, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                        """,
                        (user_id, s.title, s.action, s.category, s.monthly_saving_kg, reward, now)
                    )
            await db.commit()

orchestrator = AgentOrchestrator()
