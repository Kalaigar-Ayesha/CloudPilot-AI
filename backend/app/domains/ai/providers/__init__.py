# Import concrete LLM provider implementations to trigger their registration on application load
from app.domains.ai.providers.openai import OpenAIProvider
from app.domains.ai.providers.anthropic import AnthropicProvider
from app.domains.ai.providers.gemini import GeminiProvider
from app.domains.ai.providers.ollama import OllamaProvider
from app.domains.ai.providers.openrouter import OpenRouterProvider
