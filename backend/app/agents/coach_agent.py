"""
Coach Agent — Stage 3 (final) of the AI coaching pipeline.

Receives AnalysisResult and PlanResult and streams a personalised
coaching message to the user via Server-Sent Events. Unlike the other
agents, this agent uses standard streaming generation rather than
function calling, so its output is natural language, not structured JSON.
"""

import json
from typing import AsyncGenerator
from app.models.schemas import UserContext, AnalysisResult, PlanResult
from app.services import gemini_service

class CoachAgent:
    """Delivers personalised sustainability coaching via streaming SSE."""
    async def coach_stream(
        self,
        context: UserContext,
        analysis: AnalysisResult,
        plan: PlanResult
    ) -> AsyncGenerator[str, None]:
        """
        Stream a personalised coaching message based on analysis and plan.

        Args:
            context:  UserContext including profile and progress vs baseline.
            analysis: AnalysisResult from AnalystAgent.
            plan:     PlanResult from PlannerAgent.

        Yields:
            str: Individual text tokens as they arrive from the Gemini API.
                 The caller is responsible for SSE framing.
        """
        user_name = context.profile.name
        
        system_prompt = f"""You are {user_name}'s personal sustainability coach.
Tone: warm, expert, specific, encouraging. NOT preachy.
You have just analyzed their footprint. Reference their real data.
Format your response using Markdown with bold headings, bullet points, and clear structure.

Structure your response EXACTLY like this:
### 📊 What I'm Seeing
[Bullet point list of specific observations using their real numbers and highest impact categories]

### 🎯 Your Highest-Impact Next Step
[Detailed description of the single most impactful action from the plan, its difficulty, and exact CO2 savings]

### 🚀 Momentum & Progress
[Motivational paragraph referencing their progress vs baseline]

### 📋 New Mission Unlocked
[Brief mention of the new Mission Center challenge they should accept to start tracking this goal]
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
