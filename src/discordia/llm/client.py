# src/discordia/llm/client.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discordia.exceptions import ContextTooLargeError, LLMAPIError

if TYPE_CHECKING:
    from discordia.models.message import DiscordMessage

logger = logging.getLogger("discordia.llm_client")


class LLMClient:
    """LLM client for generating responses via Anthropic Claude.

    This wrapper is intentionally light on provider-specific details so it can
    be mocked easily in tests. It performs runtime imports of optional SDK
    dependencies to keep module import side-effects minimal.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        """Initialize LLM client.

        Args:
            api_key: Anthropic API key.
            model: Model identifier to use.
        """

        self.api_key = api_key
        self.model = model

    def _format_messages_for_llm(self, messages: list[DiscordMessage]) -> list[dict[str, str]]:
        """Convert Discord messages into a provider-friendly chat format."""

        return [{"role": "user", "content": msg.content} for msg in messages]

    async def _call_provider(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        max_tokens: int,
    ) -> Any:
        """Call the configured provider.

        This method exists primarily to isolate provider SDK concerns and make
        the client easy to mock.
        """

        try:
            from anthropic import AsyncAnthropic  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            raise LLMAPIError("Anthropic SDK is not installed", cause=e) from e

        client = AsyncAnthropic(api_key=self.api_key)
        return await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
            system=system_prompt,
        )

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Extract response text from the provider response."""

        # Anthropic responses typically look like:
        #   response.content -> list[TextBlock] where TextBlock.text holds the text
        try:
            content = getattr(response, "content", None)
            if isinstance(content, list) and content:
                first = content[0]
                text = getattr(first, "text", None)
                if isinstance(text, str):
                    return text
                if isinstance(first, dict) and isinstance(first.get("text"), str):
                    return str(first["text"])
        except Exception:
            # Fall through to generic stringification.
            pass

        return str(response)

    async def generate_response(
        self,
        context_messages: list[DiscordMessage],
        system_prompt: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """Generate an LLM response given conversation context.

        Args:
            context_messages: Recent messages for context.
            system_prompt: Optional system prompt.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated response text.

        Raises:
            LLMAPIError: When the provider call fails.
            ContextTooLargeError: When context exceeds model limits.
        """

        if not context_messages:
            logger.warning("No context messages provided")
            return "There is no context to respond to."

        system = system_prompt or "You are a helpful Discord bot assistant."
        formatted = self._format_messages_for_llm(context_messages)

        try:
            response = await self._call_provider(
                formatted,
                system_prompt=system,
                max_tokens=max_tokens,
            )
            text = self._extract_text(response)
            logger.info("Generated response (%s chars)", len(text))
            return text
        except (ContextTooLargeError, LLMAPIError):
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if any(term in error_msg for term in ("context", "token", "length", "too long")):
                raise ContextTooLargeError(
                    f"Context exceeds model limits ({len(context_messages)} messages)",
                    cause=e,
                ) from e
            raise LLMAPIError("Failed to generate LLM response", cause=e) from e

    async def summarize(self, messages: list[DiscordMessage]) -> str:
        """Summarize a conversation using the configured model."""

        return await self.generate_response(
            messages,
            system_prompt="Summarize the following conversation concisely.",
        )
