
"""
Model Registry - Central configuration for all LLM providers and models.

To add a new model:
1. Add the provider to PROVIDERS (if new)
2. Add the model to AVAILABLE_MODELS with the correct provider key
3. Ensure the corresponding API key env var is in .env
4. No code changes needed in voting, routers, or frontend!
"""

PROVIDERS = {
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    # "mistral": "MISTRAL_API_KEY",  # for adding new keys 
}

AVAILABLE_MODELS = {
    # Google
    "gemini-1.5-flash": "google",
    "gemini-1.5-pro": "google",
    "gemini-2.0-flash": "google",
    
    # OpenAI
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    
    # Groq
    "llama-3.3-70b-versatile": "groq",
    "mixtral-8x7b-32768": "groq",
    
    # Anthropic
    "claude-sonnet-4-20250514": "anthropic",
}

DEFAULT_ACTIVE_MODELS = ["gemini-2.0-flash", "llama-3.3-70b-versatile"]

# Max number of models for UI to work
MAX_ACTIVE_MODELS = 4


from typing import Optional, List


def get_provider_for_model(model_id: str) -> Optional[str]:
    return AVAILABLE_MODELS.get(model_id)


def get_env_var_for_model(model_id: str) -> Optional[str]:
    provider = get_provider_for_model(model_id)
    if provider:
        return PROVIDERS.get(provider)
    return None


def get_models_for_provider(provider: str) -> List[str]:
    return [m for m, p in AVAILABLE_MODELS.items() if p == provider]
