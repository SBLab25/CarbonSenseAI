import json
from typing import AsyncGenerator
from app.models.schemas import UserContext, AnalysisResult, PlanResult
from app.services import gemini_service

class CoachAgent:
    async def coach_stream(
        self,
        context: UserContext,
        analysis: AnalysisResult,
        plan: PlanResult
    ) -> AsyncGenerator[str, None]:
        user_name = context.profile.name
        
        system_prompt = f"""You are {user_name}'s personal sustainability coach.
Tone: warm, expert, specific, encouraging. NOT preachy.
You have just analyzed their footprint. Reference their real data.
Keep response to 150-200 words.
Structure:
1) Specific observation using their real numbers.
2) The single most impactful action from the plan.
3) Motivational close referencing their progress vs baseline.
4) Brief mention of the Mission Center challenge available.
"""
        
        # Sort plan strategies by monthly saving descending and take top 2
        sorted_strategies = sorted(plan.strategies, key=lambda s: s.monthly_saving_kg, reverse=True)
        top_strategies = sorted_strategies[:2]
        
        user_message_dict = {
            "analysis": analysis.model_dump(),
            "top_strategies": [s.model_dump() for s in top_strategies],
            "progress_pct": context.progress_pct
        }
        
        user_message = json.dumps(user_message_dict, default=str)
        
        # Stream the response tokens using stream_generate
        async for token in gemini_service.stream_generate(
            system_prompt=system_prompt,
            user_message=user_message
        ):
            yield token
