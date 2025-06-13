"""
Adaptador para Google Gemini API utilizando LangChain.

Este adaptador implementa la interfaz de IA para comunicarse con Google Gemini
a través del ecosistema de LangChain, manejando la complejidad subyacente.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone # ADDED timezone
from typing import Any, Dict, Optional
from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
# LangChainError puede no estar en la ruta directa, usamos Exception como fallback genérico
# from langchain_core.exceptions import LangChainError 

from ..core.domain_models.ai_models import (
    AIInteractionLog,
    AIModelType,
    AIProcessingStage,
    AISystemMetrics,
)
from ..core.exceptions import (
    AIServiceError,
    RateLimitError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    """Estados del circuit breaker."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker para proteger contra fallos de API."""
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None # This will store timezone-aware datetime
        self.state = CircuitBreakerState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc) # MODIFIED
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        elapsed = datetime.now(timezone.utc) - self.last_failure_time # MODIFIED
        return elapsed.total_seconds() >= self.timeout_seconds


class RateLimiter:
    """Rate limiter para controlar la frecuencia de requests a Gemini API."""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.time()
            time_elapsed = now - self.last_refill
            tokens_to_add = int(time_elapsed * (self.requests_per_minute / 60.0))
            if tokens_to_add > 0:
                self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
                self.last_refill = now
            if self.tokens > 0:
                self.tokens -= 1
                return True
            return False

    async def wait_for_token(self) -> None:
        while not await self.acquire():
            await asyncio.sleep(1.0)


class GeminiAdapter:
    """Adaptador para Google Gemini API a través de LangChain."""
    def __init__(
        self,
        api_key: str,
        model_type: AIModelType = AIModelType.GEMINI_PRO,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        requests_per_minute: int = 60
    ):
        self.api_key = api_key
        self.model_type = model_type
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

        self.model = ChatGoogleGenerativeAI(
            model=model_type.value,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60,
            expected_exception=Exception  # Usar Exception genérica por ahora
        )
        
        self._metrics = AISystemMetrics(
            avg_response_time_ms=0.0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            total_tokens_used=0,
            avg_tokens_per_request=0.0,
            avg_confidence_score=0.0,
            rate_limit_hits=0
        )

    async def generate_text(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        if not self.circuit_breaker.can_execute():
            raise AIServiceError("Circuit breaker is open - service unavailable")

        await self.rate_limiter.wait_for_token()
        
        start_time = time.time()
        
        try:
            full_prompt = self._build_prompt(prompt, context)
            
            chain = self.model | StrOutputParser()
            
            response = await asyncio.wait_for(
                chain.ainvoke(full_prompt),
                timeout=self.timeout_seconds
            )
            
            self.circuit_breaker.record_success()
            execution_time = (time.time() - start_time) * 1000
            
            self._update_metrics(
                execution_time=execution_time,
                success=True,
                tokens_used=self._estimate_tokens(full_prompt + response)
            )
            
            return response
            
        except asyncio.TimeoutError:
            self.circuit_breaker.record_failure()
            self._update_metrics(execution_time=0, success=False)
            raise TimeoutError(f"Gemini request timed out after {self.timeout_seconds}s")
            
        except Exception as e: # Captura genérica, incluye errores de LangChain
            self.circuit_breaker.record_failure()
            self._update_metrics(execution_time=0, success=False)
            if "429" in str(e) or "ResourceExhausted" in str(e):
                 raise RateLimitError(f"Gemini rate limit exceeded: {str(e)}")
            raise AIServiceError(f"Gemini API error via LangChain: {str(e)}")

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        if not context:
            return prompt
        
        context_str = "\n".join([
            f"**{key.upper()}:**\n{value}\n"
            for key, value in context.items()
        ])
        
        return f"""{context_str}\n\n**TASK:**\n{prompt}"""

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _update_metrics(
        self,
        execution_time: float,
        success: bool,
        tokens_used: int = 0
    ) -> None:
        total_requests = self._metrics.total_requests + 1
        successful_requests = self._metrics.successful_requests + (1 if success else 0)
        failed_requests = self._metrics.failed_requests + (0 if success else 1)
        total_tokens = self._metrics.total_tokens_used + tokens_used
        
        avg_response_time = self._metrics.avg_response_time_ms
        if success and execution_time > 0:
            avg_response_time = (
                (self._metrics.avg_response_time_ms * self._metrics.successful_requests + execution_time)
                / successful_requests
            )
        
        avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0.0
        
        self._metrics = AISystemMetrics(
            avg_response_time_ms=avg_response_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_tokens_used=total_tokens,
            avg_tokens_per_request=avg_tokens_per_request,
            avg_confidence_score=self._metrics.avg_confidence_score,
            rate_limit_hits=self._metrics.rate_limit_hits,
            measured_at=datetime.now(timezone.utc) # MODIFIED
        )

    def get_metrics(self) -> AISystemMetrics:
        return self._metrics

    def reset_metrics(self) -> None:
        self._metrics = AISystemMetrics()

    def get_status(self) -> Dict[str, Any]:
        return {
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "rate_limiter_tokens": self.rate_limiter.tokens,
            "model_type": self.model_type.value,
            "metrics": self._metrics.dict(),
            "healthy": self.circuit_breaker.state != CircuitBreakerState.OPEN
        }

    async def create_interaction_log(
        self,
        request_id: UUID,
        interaction_type: str,
        stage: AIProcessingStage,
        prompt_template: str,
        prompt_variables: Dict[str, Any],
        rendered_prompt: str,
        ai_response: str,
        execution_time_ms: float
    ) -> AIInteractionLog:
        tokens_input = self._estimate_tokens(rendered_prompt)
        tokens_output = self._estimate_tokens(ai_response)
        
        return AIInteractionLog(
            request_id=request_id,
            interaction_type=interaction_type,
            stage=stage,
            prompt_template=prompt_template,
            prompt_variables=prompt_variables,
            rendered_prompt=rendered_prompt,
            ai_response=ai_response,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            model_used=self.model_type,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc) # MODIFIED
        )

def create_gemini_adapter(
    api_key: str,
    model_type: AIModelType = AIModelType.GEMINI_PRO,
    **kwargs
) -> GeminiAdapter:
    return GeminiAdapter(
        api_key=api_key,
        model_type=model_type,
        **kwargs
    )
