import json
from typing import AsyncGenerator
from app.db.database import get_user_context
from app.agents.baseline_agent import BaselineAgent
from app.agents.analyst_agent import AnalystAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.coach_agent import CoachAgent
from app.services.insights_cache import insights_cache
from app.models.schemas import AnalysisResult, PlanResult, GeminiError

class AgentOrchestrator:
    def __init__(self):
        self.baseline_agent = BaselineAgent()
        self.analyst_agent = AnalystAgent()
        self.planner_agent = PlannerAgent()
        self.coach_agent = CoachAgent()
        self.cache = insights_cache

    async def run_pipeline(self, user_id: str) -> AsyncGenerator[str, None]:
        try:
            context = await get_user_context(user_id)
            
            # Analyst Cache check
            analyst_json = await self.cache.get(user_id, "analyst")
            if analyst_json:
                analysis = AnalysisResult.model_validate_json(analyst_json)
            else:
                analysis = await self.analyst_agent.analyze(context)
                await self.cache.set(user_id, "analyst", analysis.model_dump_json())
                
            # Planner Cache check
            planner_json = await self.cache.get(user_id, "planner")
            if planner_json:
                plan = PlanResult.model_validate_json(planner_json)
            else:
                plan = await self.planner_agent.plan(context, analysis)
                await self.cache.set(user_id, "planner", plan.model_dump_json())
                
            # Coach stream
            async for token in self.coach_agent.coach_stream(context, analysis, plan):
                yield token
                
        except GeminiError:
            yield "[ERROR] Analysis temporarily unavailable."
        except Exception:
            yield "[ERROR] Analysis temporarily unavailable."

orchestrator = AgentOrchestrator()
