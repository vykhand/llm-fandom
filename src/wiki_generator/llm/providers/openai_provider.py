"""OpenAI provider implementation."""

from typing import Any, Dict, Optional, Type, TypeVar

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from .base import LLMProvider, LLMResponse


T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str, **kwargs: Any):
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key, timeout=self.timeout)
        self.instructor_client = instructor.from_openai(
            AsyncOpenAI(api_key=api_key, timeout=self.timeout)
        )

    @property
    def name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens
                if response.usage
                else 0,
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.instructor_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            response_model=response_model,
        )

        return response

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the client."""
        await self.client.close()
