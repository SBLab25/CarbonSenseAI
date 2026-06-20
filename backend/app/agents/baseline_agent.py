"""
Baseline Agent — runs once at user onboarding.

Estimates the user's monthly CO₂ footprint from their lifestyle profile
before any activities are logged. This establishes the reference point
for all future progress calculations.
"""

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
    """Estimates initial carbon footprint from a lifestyle profile."""
    async def estimate(self, profile: UserProfile) -> FootprintSummary:
        """
        Estimate monthly CO₂ footprint from the user's onboarding profile.

        Args:
            profile: UserProfile populated from the onboarding wizard.

        Returns:
            FootprintSummary with estimated monthly totals per category
            (transport, energy, food, shopping) and an overall total.

        Raises:
            GeminiError: If the Gemini function call fails or returns
                         a response that fails schema validation.
        """
        system_prompt = """You are a carbon footprint estimator. Given a user's lifestyle profile,
estimate their monthly carbon footprint using standard emission factors.
India electricity grid: 0.708 kg CO2/kWh. Car: ~0.21 kg/km.
Average Indian: 158 kg CO2/month. Be conservative — underestimate is better than overestimate.
"""
        
        # Serialize profile fields manually or via model_dump
        profile_json = json.dumps(profile.model_dump(), default=str)
        
        try:
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
        except Exception as e:
            print(f"Fallback baseline calculation used due to AI error: {e}")
            transport_kg = float(profile.weekly_transport_km or 0) * 4 * 0.21
            energy_kg = float(profile.monthly_electricity_kwh or 0) * 0.708
            diet_multipliers = {"Vegan": 100, "Vegetarian": 120, "Mixed": 180, "High Meat": 250}
            food_kg = float(diet_multipliers.get(profile.diet_type, 180))
            shopping_kg = 50.0
            total_kg = transport_kg + energy_kg + food_kg + shopping_kg
            
            return FootprintSummary(
                total_kg=total_kg,
                transport_kg=transport_kg,
                energy_kg=energy_kg,
                food_kg=food_kg,
                shopping_kg=shopping_kg
            )
