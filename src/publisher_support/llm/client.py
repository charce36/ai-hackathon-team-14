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
    # Anthropic requiere 'required' explícito en object schemas
    props = schema.get("properties", {})
    schema["required"] = list(props.keys())
    schema["additionalProperties"] = False
    return {
        "name": tool_name,
        "description": f"Structured output for {tool_name}. Debes completar TODOS los campos.",
        "input_schema": schema,
    }


async def invoke_structured(
    *,
    system: str,
    user: str,
    output_model: type[T],
    tool_name: str,
    max_tokens: int | None = None,
) -> T:
    require_api_key()
    client = get_anthropic_client()
    tool = _tool_schema(output_model, tool_name)
    tokens = max_tokens or settings.claude_max_tokens

    messages: list[dict] = [{"role": "user", "content": user}]
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            response = await client.messages.create(
                model=settings.claude_model,
                max_tokens=tokens,
                temperature=0,
                system=system,
                messages=messages,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == tool_name:
                    return output_model.model_validate(block.input)

            raise LLMInvocationError(
                f"Claude no devolvió tool_use '{tool_name}' (intento {attempt + 1})"
            )
        except LLMConfigurationError:
            raise
        except ValidationError as exc:
            last_error = LLMInvocationError(f"Salida inválida del modelo: {exc}")
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"La respuesta anterior fue inválida: {exc}. "
                        f"Volvé a llamar la tool '{tool_name}' con TODOS los campos requeridos, "
                        "incluyendo files (array con al menos un objeto path/action/content) "
                        "y reasoning (string no vacío)."
                    ),
                }
            )
        except anthropic.APIError as exc:
            last_error = LLMInvocationError(f"Error Anthropic API: {exc}")
        except Exception as exc:
            last_error = LLMInvocationError(f"Error invocando Claude: {exc}")

        if attempt < 2:
            await asyncio.sleep(0.8)

    raise last_error or LLMInvocationError("Error desconocido invocando Claude")
