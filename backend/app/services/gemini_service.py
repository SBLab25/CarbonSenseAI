"""
Gemini Service — unified interface for all AI provider API calls.

Supports multiple providers (Gemini, Groq, OpenAI, Anthropic, OpenRouter)
with per-request provider selection via the X-AI-Provider header.
All agent files call this service exclusively — no agent imports an AI
SDK directly.
"""
import json
import asyncio
from typing import AsyncGenerator
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None
from openai import AsyncOpenAI
import google.generativeai as genai

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

from app.config import settings
from app.models.schemas import GeminiError
from app.services.context import ai_config_ctx

genai.configure(api_key=settings.gemini_api_key)

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

def convert_to_openai_schema(schema: dict) -> dict:
    """
    Convert a Gemini-style function schema to OpenAI JSON Schema format.

    Gemini uses uppercase type strings ("STRING", "NUMBER"); OpenAI uses
    lowercase ("string", "number"). This normalises schemas for providers
    that follow the OpenAI spec (Groq, OpenRouter, OpenAI).

    Args:
        schema: A Gemini-format function parameter schema dict.

    Returns:
        A copy of the schema with all type strings lowercased.
    """
    import copy
    new_schema = copy.deepcopy(schema)
    if "type" in new_schema and isinstance(new_schema["type"], str):
        new_schema["type"] = new_schema["type"].lower()
    
    if "properties" in new_schema:
        for k, v in new_schema["properties"].items():
            if "type" in v:
                t = v["type"].upper()
                if t == "STRING":
                    v["type"] = "string"
                elif t == "NUMBER":
                    v["type"] = "number"
                elif t == "BOOLEAN":
                    v["type"] = "boolean"
                elif t == "INTEGER":
                    v["type"] = "integer"
                elif t == "ARRAY":
                    v["type"] = "array"
                elif t == "OBJECT":
                    v["type"] = "object"
            if "items" in v:
                v["items"] = convert_to_openai_schema(v["items"])
    
    return new_schema

def get_ai_client_info():
    config = ai_config_ctx.get()
    provider = config.get("provider", "groq").lower()
    api_key = config.get("api_key")
    model = config.get("model")

    if not api_key:
        if provider == "groq": api_key = settings.groq_api_key
        elif provider == "openrouter": api_key = settings.groq_api_key if settings.groq_api_key.startswith("sk-or-") else None
        elif provider == "gemini": api_key = settings.gemini_api_key
        elif provider == "openai": api_key = getattr(settings, "openai_api_key", None)
        elif provider == "anthropic": api_key = getattr(settings, "anthropic_api_key", None)

    if not model:
        if provider == "groq": model = "openai/gpt-oss-120b"
        elif provider == "openrouter": model = "nvidia/nemotron-4-340b-instruct"
        elif provider == "gemini": model = "gemini-1.5-flash"
        elif provider == "openai": model = "gpt-4o-mini"
        elif provider == "anthropic": model = "claude-3-5-sonnet-20241022"

    return provider, api_key, model

async def function_call_primary(system_prompt: str, user_message: str, function_schema: dict) -> dict:
    provider, api_key, model = get_ai_client_info()
    
    if provider == "anthropic" and AsyncAnthropic:
        client = AsyncAnthropic(api_key=api_key)
        tool = {
            "name": function_schema.get("name", "function"),
            "description": function_schema.get("description", ""),
            "input_schema": convert_to_openai_schema(function_schema.get("parameters", {}))
        }
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]}
        )
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        raise ValueError("No function call returned by Anthropic")
    
    elif provider == "gemini":
        return await function_call_gemini(system_prompt, user_message, function_schema, api_key, model)

    else:
        # OpenAI compatibility format
        if provider == "openai":
            client = AsyncOpenAI(api_key=api_key)
        elif provider == "openrouter":
            client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        else: # groq
            client = AsyncGroq(api_key=api_key)

        tool = {
            "type": "function",
            "function": {
                "name": function_schema.get("name", "function"),
                "description": function_schema.get("description", ""),
                "parameters": convert_to_openai_schema(function_schema.get("parameters", {}))
            }
        }
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": tool["function"]["name"]}}
        )
        message = response.choices[0].message
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return json.loads(tool_call.function.arguments)
        elif message.content:
            try:
                return json.loads(message.content)
            except json.JSONDecodeError:
                pass
        raise ValueError("No function call returned")

async def function_call_gemini(system_prompt: str, user_message: str, function_schema: dict, api_key: str = None, model_name: str = "gemini-1.5-flash") -> dict:
    if api_key:
        genai.configure(api_key=api_key)
    prompt = f"{system_prompt}\n\nYou MUST respond with ONLY a valid JSON object matching this schema:\n{json.dumps(function_schema)}\n\nUser input: {user_message}"
    model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
    response = await model.generate_content_async(prompt)
    if not response.text:
        raise ValueError("Empty response from Gemini")
    return json.loads(response.text)

async def function_call(system_prompt: str, user_message: str, function_schema: dict) -> dict:
    max_retries = 2
    for attempt in range(max_retries):
        try:
            return await function_call_primary(system_prompt, user_message, function_schema)
        except Exception as e_primary:
            print(f"API failed: {e_primary}. Attempt {attempt+1}/{max_retries}")
            if attempt == max_retries - 1:
                raise GeminiError("Analysis temporarily unavailable.", f"API failed: {e_primary}")
            await asyncio.sleep(2)

async def stream_generate(system_prompt: str, user_message: str, history=None) -> AsyncGenerator[str, None]:
    provider, api_key, model = get_ai_client_info()

    try:
        if provider == "anthropic" and AsyncAnthropic:
            client = AsyncAnthropic(api_key=api_key)
            messages = []
            if history:
                for h in history:
                    role = "assistant" if h.get("role") in ["model", "assistant", "coach"] else "user"
                    content = h.get("content", "")
                    if content:
                        messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": user_message})
            
            async with client.messages.stream(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        elif provider == "gemini":
            if api_key:
                genai.configure(api_key=api_key)
            gemini_history = []
            if history:
                for h in history:
                    role = "model" if h.get("role") in ["model", "assistant", "coach"] else "user"
                    gemini_history.append({"role": role, "parts": [h.get("content", "")]})
            
            g_model = genai.GenerativeModel(model, system_instruction=system_prompt)
            chat = g_model.start_chat(history=gemini_history)
            response = await chat.send_message_async(user_message, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        else:
            # OpenAI compatibility
            if provider == "openai":
                client = AsyncOpenAI(api_key=api_key)
            elif provider == "openrouter":
                client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            else: # groq
                client = AsyncGroq(api_key=api_key)

            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for h in history:
                    role = "assistant" if h.get("role") in ["model", "assistant", "coach"] else "user"
                    content = h.get("content", "")
                    if content:
                        messages.append({"role": role, "content": content})
            
            messages.append({"role": "user", "content": user_message})

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            async for chunk in response:
                try:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                except Exception:
                    continue

    except Exception as e:
        print(f"Stream error: {e}")
        yield f"[STREAM_ERROR] Coaching temporarily unavailable. Details: {e}"

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
