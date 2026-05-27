class LLMConfigurationError(Exception):
    """Raised when ANTHROPIC_API_KEY or required LLM config is missing."""


class LLMInvocationError(Exception):
    """Raised when Claude API call fails or returns invalid structured output."""
