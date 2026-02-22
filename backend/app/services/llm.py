"""
LLM Service - Abstraction for LLM operations.
"""

import asyncio
import random
import time
from typing import List, Dict, Optional, Protocol
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
import tiktoken

from app.core.config import get_settings
from app.utils.llm_logger import get_llm_logger

OPENAI_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-5-mini",
}


class LLMProvider(Protocol):
    """
    Protocol that all LLM providers must implement.
    """
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate completion from this provider's API."""
        ...
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using provider's tokenizer."""


class OpenAIProvider:
    """OpenAI provider implementation with retry logic."""

    def __init__(self, model: str):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Retry configuration
        self.max_retries = 10
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0  # Cap at 60 seconds

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Call OpenAI API with exponential backoff retry logic.
        
        Retries on:
        - Rate limits (429)
        - Timeouts
        - Server errors (500-599)
        - Connection errors
        
        Does NOT retry on:
        - Bad requests (400) - indicates bug in our code
        - Auth errors (401) - config issue        
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    # temperature=temperature,  # Not supported by gpt-5-mini
                    # max_tokens=max_tokens,    # Not supported by gpt-5-mini
                    **kwargs
                )

                result = response.choices[0].message.content.strip()
                return result
            
            except RateLimitError as e:
                print(f"  ⚠️ Rate limit hit (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    print(f"  ⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ❌ Rate limit exceeded after {self.max_retries} attempts")
                    raise

            except APITimeoutError as e:
                print(f"  ⚠️ Timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    print(f"  ⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ❌ Timeout after {self.max_retries} attempts")
                    raise

            except APIConnectionError as e:
                print(f"  ⚠️ Connection error (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    print(f"  ⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                else:
                    print(f"  ❌ Connection failed after {self.max_retries} attempts")
                    raise

            except APIError as e:
                # Check if it's a server error (500-599)
                if hasattr(e, 'status_code') and 500 <= e.status_code < 600:
                    print(f"  ⚠️ Server error {e.status_code} (attempt {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        delay = self._calculate_delay(attempt)
                        print(f"  ⏳ Waiting {delay:.1f}s before retry...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"  ❌ Server error after {self.max_retries} attempts")
                        raise
                else:
                    # Client error (400, 401, 404, etc.) - don't retry
                    print(f"  ❌ API error ({e}): {e}")
                    raise

            except Exception as e:
                print(f"  ❌ Unexpected error ({type(e).__name__}): {e}")
                raise                

        # Should never reach here, but just in case
        raise Exception(f"Failed after {self.max_retries} attempts")
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter and max cap.
        
        Formula: min(base_delay * (2 ** attempt), max_delay) + jitter
        """            
        exponential_delay = self.base_delay * (2**attempt)
        capped_delay = min(exponential_delay, self.max_delay)
        jitter = random.uniform(0., 0.5)
        return capped_delay + jitter
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    

def get_provider(model: str) -> LLMProvider:
    """
    Factory function to get the appropriate provider for a model.
    """    
    if model in OPENAI_MODELS:
        return OpenAIProvider(model)

    # elif model in ANTHROPIC_MODELS:
        # return ...
    
    else:
        raise ValueError(
            f"Unsupported model: {model}. "
            f"Supported OpenAI models: {', '.join(OPENAI_MODELS)}"
        )
    

class LLMService:
    """
    High-level service for LLM operations with retry logic.
    """

    def __init__(self):
        self._provider_cache: Dict[str, LLMProvider] = {}

    def _get_provider(self, model: str) -> LLMProvider:
        """Get provider for model (cached)."""
        if model not in self._provider_cache:
            self._provider_cache[model] = get_provider(model)
        return self._provider_cache[model]
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-5-mini",
        temperature: float = 0.7,  # Ignored by gpt-5-mini
        max_tokens: int = 2000,    # Ignored by gpt-5-mini
        log_source: Optional[str] = None,
        case_id: Optional[int] = None,
        logger = None,
        **kwargs,
    ) -> str:
        """
        Generate completion from LLM with automatic retries.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            log_source: Optional description for logging (e.g., "Planner - Step 1")
            case_id: Optional case ID for logging
            logger: Optional LLMCallLogger instance for this request
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text completion
        """
        start_time = time.time()
        provider = self._get_provider(model)
        
        try:
            response = await provider.complete(messages, temperature, max_tokens, **kwargs)
            duration = time.time() - start_time
            
            # Log the call if logger and source are provided
            if logger and log_source:
                await logger.log_call(
                    source=log_source,
                    prompt=messages,
                    response=response,
                    metadata={
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "duration_seconds": round(duration, 2),
                        "response_length": len(response)
                    },
                    case_id=case_id
                )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            
            # Log failed calls too
            if logger and log_source:
                await logger.log_call(
                    source=f"{log_source} [FAILED]",
                    prompt=messages,
                    response=f"ERROR: {type(e).__name__}: {str(e)}",
                    metadata={
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "duration_seconds": round(duration, 2),
                        "status": "failed",
                        "error_type": type(e).__name__
                    },
                    case_id=case_id
                )
            
            raise
    
    def count_tokens(
        self,
        text: str,
        model: str = "gpt-4o-mini"
    ) -> int:
        """Count tokens in text for a specific model."""
        provider = self._get_provider(model)
        return provider.count_tokens(text)
    
    def count_message_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini"
    ) -> int:
        """
        Count tokens in a list of messages.
        """
        provider = self._get_provider(model)
        # Rough estimate
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # Message formatting overhead
            for key, value in message.items():
                num_tokens += provider.count_tokens(str(value))
            num_tokens += 2  # Reply primer
            return num_tokens
        

# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get singleton LLM service instance.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service