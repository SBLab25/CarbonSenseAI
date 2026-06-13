import json
from app.models.schemas import UserContext, AnalysisResult, HotspotDetail
from app.services import gemini_service

ANALYZE_SCHEMA = {
    "name": "analyze_carbon_footprint",
    "description": "Analyze actual activity data and calculate carbon footprint hotspots and behavior patterns.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "primary_hotspot": {
                "type": "STRING",
                "description": "The category with the highest carbon emissions."
            },
            "hotspots": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "category": {
                            "type": "STRING",
                            "description": "Category of the hotspot (transport, energy, food, shopping)."
                        },
                        "pct_of_total": {
                            "type": "NUMBER",
                            "description": "Percentage of total emissions."
                        },
                        "vs_baseline_change_pct": {
                            "type": "NUMBER",
                            "description": "Percentage change compared to user's baseline."
                        },
                        "key_behaviors": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "Observed behaviors driving this hotspot."
                        },
                        "reduction_opportunity_kg": {
                            "type": "NUMBER",
                            "description": "Potential monthly savings in kg CO2."
                        }
                    },
                    "required": ["category", "pct_of_total", "vs_baseline_change_pct", "key_behaviors", "reduction_opportunity_kg"]
                }
            },
            "behavioral_patterns": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Top key behavioral patterns observed (maximum 3)."
            },
            "quick_win_available": {
                "type": "BOOLEAN",
                "description": "Whether a low-effort high-impact action is available."
            },
            "analysis_confidence": {
                "type": "STRING",
                "description": "Confidence level based on logged activities count.",
                "enum": ["high", "medium", "low"]
            }
        },
        "required": [
            "primary_hotspot",
            "hotspots",
            "behavioral_patterns",
            "quick_win_available",
            "analysis_confidence"
        ]
    }
}

class AnalystAgent:
    async def analyze(self, context: UserContext) -> AnalysisResult:
        system_prompt = """You are a carbon footprint analyst. Analyze actual activity data.
Be specific — reference actual activities logged, not generic observations.
Confidence: high if 20+ activities, medium if 5-19, low if fewer than 5.
"""
        
        user_message_dict = {
            "profile": context.profile.model_dump(),
            "baseline_footprint": context.baseline_footprint.model_dump(),
            "current_footprint": context.current_footprint.model_dump(),
            "recent_activities": context.recent_activities,
            "progress_pct": context.progress_pct
        }
        
        user_message = json.dumps(user_message_dict, default=str)
        
        result = await gemini_service.function_call(
            system_prompt=system_prompt,
            user_message=user_message,
            function_schema=ANALYZE_SCHEMA
        )
        
        # Parse hotspots into HotspotDetail objects
        hotspots = []
        for h in result.get("hotspots", []):
            hotspots.append(HotspotDetail(
                category=h.get("category", ""),
                pct_of_total=float(h.get("pct_of_total", 0.0)),
                vs_baseline_change_pct=float(h.get("vs_baseline_change_pct", 0.0)),
                key_behaviors=h.get("key_behaviors", []),
                reduction_opportunity_kg=float(h.get("reduction_opportunity_kg", 0.0))
            ))
            
        return AnalysisResult(
            primary_hotspot=result.get("primary_hotspot", ""),
            hotspots=hotspots,
            behavioral_patterns=result.get("behavioral_patterns", [])[:3],
            quick_win_available=bool(result.get("quick_win_available", False)),
            analysis_confidence=result.get("analysis_confidence", "low")
        )
