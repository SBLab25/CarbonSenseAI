import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from typing import AsyncGenerator
from app.config import settings
from app.models.schemas import GeminiError

genai.configure(api_key=settings.gemini_api_key)
MODEL_NAME = "gemini-2.0-flash"

NL_PARSE_SCHEMA = {
    "name": "parse_carbon_activity",
    "description": "Parse a carbon-emitting activity description from natural language.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "description": "The category of activity (transport, energy, food, shopping).",
                "enum": ["transport", "energy", "food", "shopping"]
            },
            "type": {
                "type": "STRING",
                "description": "The specific type of activity. Transport: car_petrol, car_diesel, car_electric, bus, train, flight_domestic, flight_international, motorcycle, bicycle, walking. Energy: electricity, natural_gas, lpg. Food: beef, lamb, pork, chicken, fish, dairy, eggs, vegetables, fruits, grains, legumes. Shopping: electronics, clothing, household_item."
            },
            "amount": {
                "type": "NUMBER",
                "description": "The numeric amount of the activity."
            },
            "unit": {
                "type": "STRING",
                "description": "The unit of measurement (km for transport, kWh for energy, kg for food, item for shopping)."
            },
            "confidence": {
                "type": "STRING",
                "description": "Confidence of the parsing (high, medium, low).",
                "enum": ["high", "medium", "low"]
            }
        },
        "required": ["category", "type", "amount", "unit", "confidence"]
    }
}

async def function_call(system_prompt: str, user_message: str, function_schema: dict) -> dict:
    try:
        tool_config = {
            "function_calling_config": {
                "mode": "ANY"
            }
        }
        
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=system_prompt,
            tools=[function_schema]
        )
        
        response = await model.generate_content_async(
            user_message,
            tool_config=tool_config
        )
        
        if not response.candidates:
            raise GeminiError("Analysis temporarily unavailable. Please try again.", "Response blocked or empty candidates")
            
        candidate = response.candidates[0]
        if candidate.finish_reason and candidate.finish_reason.name in ["SAFETY", "RECITATION", "OTHER"]:
            raise GeminiError("Analysis temporarily unavailable. Please try again.", f"Response blocked by finish reason: {candidate.finish_reason.name}")
            
        if not candidate.content or not candidate.content.parts:
            raise GeminiError("Analysis temporarily unavailable. Please try again.", "No parts in response candidate content")
            
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                args = {}
                for k, v in part.function_call.args.items():
                    args[k] = v
                return args
                
        raise GeminiError("Analysis temporarily unavailable. Please try again.", "No function call part found in response")
        
    except GoogleAPIError as e:
        raise GeminiError("Analysis temporarily unavailable. Please try again.", f"Google API error: {str(e)}")
    except Exception as e:
        if isinstance(e, GeminiError):
            raise e
        raise GeminiError("Analysis temporarily unavailable. Please try again.", f"Unexpected error during function call: {str(e)}")

async def stream_generate(system_prompt: str, user_message: str, history=None) -> AsyncGenerator[str, None]:
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=system_prompt
        )
        
        formatted_history = []
        if history:
            for h in history:
                role = h.get("role", "user")
                if role in ["model", "assistant", "coach"]:
                    role = "model"
                else:
                    role = "user"
                content = h.get("content", "")
                if content:
                    formatted_history.append({
                        "role": role,
                        "parts": [content]
                    })
                    
        chat = model.start_chat(history=formatted_history)
        response = await chat.send_message_async(user_message, stream=True)
        async for chunk in response:
            try:
                if chunk.text:
                    yield chunk.text
            except Exception:
                yield "[STREAM_ERROR] Coaching temporarily unavailable."
                return
    except Exception:
        yield "[STREAM_ERROR] Coaching temporarily unavailable."

async def parse_activity_nl(description: str) -> dict:
    system_prompt = """You are a natural language parser for carbon-emitting activities.
Analyze the user's description and extract the activity category, type, amount, unit, and your confidence level.

Allowed Categories and Types:
- transport:
  * car_petrol (default for 'car' or 'drive' unless specified as diesel or electric)
  * car_diesel
  * car_electric
  * bus
  * train
  * flight_domestic (flight duration < 3 hours or domestic flight)
  * flight_international (flight duration >= 3 hours or international flight)
  * motorcycle
  * bicycle
  * walking
- energy:
  * electricity
  * natural_gas
  * lpg
- food:
  * beef
  * lamb
  * pork
  * chicken
  * fish
  * dairy
  * eggs
  * vegetables
  * fruits
  * grains
  * legumes
- shopping:
  * electronics
  * clothing
  * household_item

Units of Measurement:
- km for transport (distance)
- kWh for energy
- kg for food (weight)
- item for shopping (quantity)

Strictly adhere to these types and units. If the user mentions 'drove 20km', category=transport, type=car_petrol, amount=20.0, unit=km.
If they say 'ate 500g of beef', category=food, type=beef, amount=0.5, unit=kg (convert grams to kg!).
If they say 'bought 2 shirts', category=shopping, type=clothing, amount=2.0, unit=item.
"""
    return await function_call(system_prompt, description, NL_PARSE_SCHEMA)
