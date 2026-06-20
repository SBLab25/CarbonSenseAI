"""
Planner Agent — Stage 2 of the AI coaching pipeline.

Receives the AnalystAgent output and generates a ranked list of
CO₂ reduction strategies tailored to the user's specific hotspots.
Output is passed to CoachAgent and used to generate Mission Center items.
"""

import json
from app.models.schemas import UserContext, AnalysisResult, PlanResult, ReductionStrategy
from app.services import gemini_service

PLANNER_SCHEMA = {
    "name": "create_reduction_plan",
    "description": "Create specific, actionable carbon reduction strategies and a monthly plan.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "strategies": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {
                            "type": "STRING",
                            "description": "Short name for the strategy."
                        },
                        "action": {
                            "type": "STRING",
                            "description": "Specific action user must take."
                        },
                        "category": {
                            "type": "STRING",
                            "description": "Category (transport, energy, food, shopping)."
                        },
                        "monthly_saving_kg": {
                            "type": "NUMBER",
                            "description": "Estimated monthly savings in kg CO2."
                        },
                        "difficulty": {
                            "type": "STRING",
                            "description": "Difficulty of the strategy (easy, medium, hard)."
                        },
                        "timeframe_days": {
                            "type": "INTEGER",
                            "description": "Days to adopt/execute this strategy."
                        },
                        "mission_type": {
                            "type": "STRING",
                            "description": "If this can be turned into a Mission Center challenge, specify the type. If not applicable, output 'none'."
                        }
                    },
                    "required": ["title", "action", "category", "monthly_saving_kg", "difficulty", "timeframe_days"]
                },
                "description": "List of EXACTLY 5 highly diverse, specific reduction strategies. Do not provide fewer than 5."
            },
            "total_potential_saving_kg": {
                "type": "NUMBER",
                "description": "Total potential carbon savings in kg."
            },
            "recommended_goal_pct": {
                "type": "NUMBER",
                "description": "Recommended carbon reduction percentage goal."
            },
            "thirty_day_focus": {
                "type": "STRING",
                "description": "The primary focus for the next 30 days."
            }
        },
        "required": [
            "strategies",
            "total_potential_saving_kg",
            "recommended_goal_pct",
            "thirty_day_focus"
        ]
    }
}

class PlannerAgent:
    """Generates personalised CO₂ reduction strategies from analyst output."""
    async def plan(self, context: UserContext, analysis: AnalysisResult) -> PlanResult:
        """
        Create a ranked reduction plan based on the analyst's findings.

        Args:
            context:  Full user context including profile and active goal.
            analysis: AnalysisResult produced by AnalystAgent.

        Returns:
            PlanResult containing 3–5 ReductionStrategy objects ranked by
            monthly CO₂ saving, plus a recommended goal percentage and
            the single highest-impact action for the next 30 days.

        Raises:
            GeminiError: If the Gemini API call fails or returns invalid data.
        """
        system_prompt = """You are a highly creative sustainability planner. Create EXACTLY 5 diverse, specific, and actionable carbon reduction strategies based strictly on the user's specific lifestyle and the analyst's findings.
Do NOT use generic templates. Provide unique ideas tailored to their primary hotspot.
Rank by monthly_saving_kg.
Difficulty: easy=habit change, medium=lifestyle change, hard=major investment.
"""
        
        user_message_dict = {
            "profile": context.profile.model_dump(),
            "primary_hotspot": analysis.primary_hotspot,
            "analysis": analysis.model_dump()
        }
        
        user_message = json.dumps(user_message_dict, default=str)
        
        result = await gemini_service.function_call(
            system_prompt=system_prompt,
            user_message=user_message,
            function_schema=PLANNER_SCHEMA
        )
        
        strategies = []
        for s in result.get("strategies", []):
            strategies.append(ReductionStrategy(
                title=s.get("title", ""),
                action=s.get("action", ""),
                category=s.get("category", ""),
                monthly_saving_kg=float(s.get("monthly_saving_kg", 0.0)),
                difficulty=s.get("difficulty", "easy"),
                timeframe_days=int(s.get("timeframe_days", 30)),
                mission_type=s.get("mission_type", None)
            ))
            
        return PlanResult(
            strategies=strategies,
            total_potential_saving_kg=float(result.get("total_potential_saving_kg", 0.0)),
            recommended_goal_pct=float(result.get("recommended_goal_pct", 15.0)),
            thirty_day_focus=result.get("thirty_day_focus", "")
        )
