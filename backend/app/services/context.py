from contextvars import ContextVar

# A dictionary to store AI configuration for the current request
# Expected keys: "provider", "api_key", "model"
ai_config_ctx: ContextVar[dict] = ContextVar("ai_config", default={})
