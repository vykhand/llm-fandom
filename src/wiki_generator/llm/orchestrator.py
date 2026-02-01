"""LLM orchestrator with multi-provider fallback."""

import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar

from loguru import logger
from pydantic import BaseModel
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core.config import Config
from .providers.anthropic_provider import AnthropicProvider
from .providers.base import LLMProvider, LLMResponse
from .providers.openai_provider import OpenAIProvider


T = TypeVar("T", bound=BaseModel)


class LLMOrchestrator:
    """Orchestrates multiple LLM providers with automatic fallback."""

    def __init__(self, config: Config):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize all configured providers."""
        for provider_config in self.config.llm.providers:
            name = provider_config["name"]
            api_key = self.config.get_api_key(provider_config["api_key_env"])

            if not api_key:
                logger.warning(
                    f"No API key found for provider {name} "
                    f"(env var: {provider_config['api_key_env']})"
                )
                continue

            provider = self._create_provider(
                name=name,
                api_key=api_key,
                model=provider_config["model"],
                max_tokens=provider_config.get("max_tokens", 4096),
                temperature=provider_config.get("temperature", 0.7),
                timeout=provider_config.get("timeout", 60),
            )

            if provider:
                self.providers[name] = provider
                logger.info(f"Initialized provider: {name} with model {provider_config['model']}")

    def _create_provider(
        self,
        name: str,
        api_key: str,
        model: str,
        **kwargs: Any,
    ) -> Optional[LLMProvider]:
        """Create a provider instance."""
        provider_map = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
        }

        provider_class = provider_map.get(name)
        if not provider_class:
            logger.error(f"Unknown provider: {name}")
            return None

        return provider_class(api_key=api_key, model=model, **kwargs)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text with automatic fallback between providers."""
        providers_to_try = self._get_provider_order(preferred_provider)

        last_error = None
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            try:
                logger.info(f"Attempting generation with provider: {provider_name}")

                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.config.llm.max_retries),
                    wait=wait_exponential(
                        multiplier=self.config.llm.retry_delay,
                        min=1,
                        max=10,
                    ),
                    retry=retry_if_exception_type((Exception,)),
                    reraise=True,
                ):
                    with attempt:
                        response = await provider.generate(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            **kwargs,
                        )
                        logger.success(
                            f"Successfully generated with {provider_name}: "
                            f"{response.usage.get('output_tokens', 0)} tokens"
                        )
                        return response

            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {str(e)}")
                last_error = e
                continue

        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured output with automatic fallback."""
        providers_to_try = self._get_provider_order(preferred_provider)

        last_error = None
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            try:
                logger.info(
                    f"Attempting structured generation with provider: {provider_name}"
                )

                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.config.llm.max_retries),
                    wait=wait_exponential(
                        multiplier=self.config.llm.retry_delay,
                        min=1,
                        max=10,
                    ),
                    retry=retry_if_exception_type((Exception,)),
                    reraise=True,
                ):
                    with attempt:
                        response = await provider.generate_structured(
                            prompt=prompt,
                            response_model=response_model,
                            system_prompt=system_prompt,
                            **kwargs,
                        )
                        logger.success(
                            f"Successfully generated structured output with {provider_name}"
                        )
                        return response

            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {str(e)}")
                last_error = e
                continue

        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _get_provider_order(self, preferred_provider: Optional[str] = None) -> List[str]:
        """Get the order of providers to try."""
        if preferred_provider and preferred_provider in self.providers:
            # Try preferred provider first, then fallback order
            order = [preferred_provider]
            for p in self.config.llm.fallback_order:
                if p != preferred_provider and p in self.providers:
                    order.append(p)
            return order

        # Use configured fallback order
        return [p for p in self.config.llm.fallback_order if p in self.providers]

    async def close(self) -> None:
        """Close all provider connections."""
        for provider in self.providers.values():
            await provider.__aexit__(None, None, None)
