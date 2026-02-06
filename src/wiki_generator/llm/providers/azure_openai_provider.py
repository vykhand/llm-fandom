"""Azure OpenAI provider implementation using LangChain."""

from typing import Any, Optional, Type, TypeVar

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from .base import LLMProvider, LLMResponse


T = TypeVar("T", bound=BaseModel)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider using LangChain with native structured outputs."""

    def __init__(self, api_key: str, model: str, **kwargs: Any):
        super().__init__(api_key, model, **kwargs)
        self.client = AzureChatOpenAI(
            azure_deployment=model,
            api_key=api_key,
            azure_endpoint=kwargs.get("azure_endpoint", ""),
            api_version=kwargs.get("api_version", "2024-02-15-preview"),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
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
        """Generate text using Azure OpenAI via LangChain."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = await self.client.ainvoke(messages)

        return LLMResponse(
            content=response.content,
            model=self.model,
            usage=dict(response.usage_metadata) if response.usage_metadata else {},
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
        """Generate structured output using LangChain with_structured_output (json_schema)."""
        structured_llm = self.client.with_structured_output(
            response_model, method="json_schema"
        )

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = await structured_llm.ainvoke(messages)
        return response

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the client."""
        pass
