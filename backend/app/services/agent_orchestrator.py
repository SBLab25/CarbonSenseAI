import json
from typing import AsyncGenerator
from app.db.database import get_user_context
from app.agents.baseline_agent import BaselineAgent
from app.agents.analyst_agent import AnalystAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.coach_agent import CoachAgent
from app.services.insights_cache import insights_cache
from app.models.schemas import AnalysisResult, PlanResult, GeminiError

import datetime

class AgentOrchestrator:
    def __init__(self):
        self.baseline_agent = BaselineAgent()
        self.analyst_agent = AnalystAgent()
        self.planner_agent = PlannerAgent()
        self.coach_agent = CoachAgent()
        self.cache = insights_cache

    async def run_pipeline(self, user_id: str) -> AsyncGenerator[str, None]:
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
        except Exception as e:
            yield f"[ERROR] System error during pipeline execution: {e}"

    async def _auto_generate_missions(self, user_id: str, plan: PlanResult):
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
