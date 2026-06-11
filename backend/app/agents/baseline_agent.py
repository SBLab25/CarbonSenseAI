import json
from app.models.schemas import UserProfile, FootprintSummary
from app.services import gemini_service

BASELINE_SCHEMA = {
    "name": "set_baseline_footprint",
    "description": "Set the estimated monthly baseline carbon footprint for the user based on profile.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "monthly_total_kg": {
                "type": "NUMBER",
                "description": "Total estimated monthly carbon footprint in kg CO2."
            },
            "transport_kg": {
                "type": "NUMBER",
                "description": "Estimated monthly transport footprint in kg CO2."
            },
            "energy_kg": {
                "type": "NUMBER",
                "description": "Estimated monthly energy footprint in kg CO2."
            },
            "food_kg": {
                "type": "NUMBER",
                "description": "Estimated monthly food footprint in kg CO2."
            },
            "shopping_kg": {
                "type": "NUMBER",
                "description": "Estimated monthly shopping footprint in kg CO2."
            },
            "primary_hotspot": {
                "type": "STRING",
                "description": "The category with the largest footprint (transport, energy, food, shopping)."
            },
            "confidence": {
                "type": "STRING",
                "description": "Confidence of the estimation (high, medium, low)."
            }
        },
        "required": [
            "monthly_total_kg",
            "transport_kg",
            "energy_kg",
            "food_kg",
            "shopping_kg",
            "primary_hotspot",
            "confidence"
        ]
    }
}

class BaselineAgent:
    async def estimate(self, profile: UserProfile) -> FootprintSummary:
        system_prompt = """You are a carbon footprint estimator. Given a user's lifestyle profile,
estimate their monthly carbon footprint using standard emission factors.
India electricity grid: 0.708 kg CO2/kWh. Car: ~0.21 kg/km.
Average Indian: 158 kg CO2/month. Be conservative — underestimate is better than overestimate.
"""
        
        # Serialize profile fields manually or via model_dump
        profile_json = json.dumps(profile.model_dump(), default=str)
        
        result = await gemini_service.function_call(
            system_prompt=system_prompt,
            user_message=profile_json,
            function_schema=BASELINE_SCHEMA
        )
        
        return FootprintSummary(
            total_kg=float(result.get("monthly_total_kg", 0.0)),
            transport_kg=float(result.get("transport_kg", 0.0)),
            energy_kg=float(result.get("energy_kg", 0.0)),
            food_kg=float(result.get("food_kg", 0.0)),
            shopping_kg=float(result.get("shopping_kg", 0.0))
        )
