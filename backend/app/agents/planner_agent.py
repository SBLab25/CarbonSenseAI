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
                            "description": "If this can be turned into a Mission Center challenge, specify the type, otherwise null."
                        }
                    },
                    "required": ["title", "action", "category", "monthly_saving_kg", "difficulty", "timeframe_days"]
                },
                "description": "List of 3 to 5 reduction strategies."
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
    async def plan(self, context: UserContext, analysis: AnalysisResult) -> PlanResult:
        system_prompt = """You are a sustainability planner. Create specific, actionable
reduction strategies based on the analyst's findings. Rank by monthly_saving_kg.
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
