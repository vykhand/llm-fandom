"""Anthropic Claude provider implementation."""

import json
from typing import Any, Dict, Optional, Type, TypeVar

import instructor
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from .base import LLMProvider, LLMResponse


T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str, model: str, **kwargs: Any):
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key, timeout=self.timeout)
        self.instructor_client = instructor.from_anthropic(
            AsyncAnthropic(api_key=api_key, timeout=self.timeout)
        )

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using Claude."""
        messages = [{"role": "user", "content": prompt}]

        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        if system_prompt:
            request_params["system"] = system_prompt

        response = await self.client.messages.create(**request_params)

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            provider=self.name,
            raw_response=response,
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured output using instructor."""
        messages = [{"role": "user", "content": prompt}]

        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "response_model": response_model,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        response = await self.instructor_client.messages.create(**request_params)
        return response

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the client."""
        await self.client.close()
