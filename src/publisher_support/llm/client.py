import asyncio
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from publisher_support.config import settings
from publisher_support.llm.errors import LLMConfigurationError, LLMInvocationError

T = TypeVar("T", bound=BaseModel)


def require_api_key() -> str:
    if not settings.anthropic_api_key:
        raise LLMConfigurationError(
            "ANTHROPIC_API_KEY no configurada. Agregala en el archivo .env"
        )
    return settings.anthropic_api_key


def get_anthropic_client() -> anthropic.AsyncAnthropic:
    require_api_key()
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


def _tool_schema(model: type[BaseModel], tool_name: str) -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)
    return {
        "name": tool_name,
        "description": f"Structured output for {tool_name}",
        "input_schema": schema,
    }


async def invoke_structured(
    *,
    system: str,
    user: str,
    output_model: type[T],
    tool_name: str,
) -> T:
    require_api_key()
    client = get_anthropic_client()
    tool = _tool_schema(output_model, tool_name)

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = await client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.claude_max_tokens,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == tool_name:
                    return output_model.model_validate(block.input)

            raise LLMInvocationError(
                f"Claude no devolvió tool_use '{tool_name}' (intento {attempt + 1})"
            )
        except (LLMConfigurationError,):
            raise
        except ValidationError as exc:
            last_error = LLMInvocationError(f"Salida inválida del modelo: {exc}")
        except anthropic.APIError as exc:
            last_error = LLMInvocationError(f"Error Anthropic API: {exc}")
        except Exception as exc:
            last_error = LLMInvocationError(f"Error invocando Claude: {exc}")

        if attempt == 0:
            await asyncio.sleep(0.5)

    raise last_error or LLMInvocationError("Error desconocido invocando Claude")
