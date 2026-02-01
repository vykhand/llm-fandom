"""Azure OpenAI provider implementation."""

from typing import Any, Dict, Optional, Type, TypeVar

import instructor
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from .base import LLMProvider, LLMResponse


T = TypeVar("T", bound=BaseModel)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str,
        azure_endpoint: str,
        api_version: str = "2024-02-15-preview",
        **kwargs: Any
    ):
        super().__init__(api_key, model, **kwargs)
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            timeout=self.timeout,
        )
        self.instructor_client = instructor.from_openai(
            AsyncAzureOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                timeout=self.timeout,
            )
        )

    @property
    def name(self) -> str:
        return "azure_openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using Azure OpenAI."""
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
