"""Thin wrapper around Perplexity's OpenAI-compatible API.

Perplexity uses the same protocol as OpenAI — just a different base_url.
The `openai` SDK is already installed (via langchain-openai).

Usage:
    client = PerplexityClient(api_key="pplx-xxx")
    result = client.research("What are current Treasury yields?")
    print(result["content"])   # The sourced answer
    print(result["citations"]) # List of source URLs
"""
import hashlib
import logging
import time

from openai import OpenAI

logger = logging.getLogger(__name__)

PERPLEXITY_BASE_URL = "https://api.perplexity.ai"


class PerplexityClient:
    """Client for the Perplexity API (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str = "sonar-pro"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=PERPLEXITY_BASE_URL,
        )
        self.model = model

    def research(
        self,
        query: str,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> dict:
        """Ask Perplexity a research question.

        Returns:
            {
                "content": "The sourced answer text...",
                "citations": ["https://source1.com", ...],
                "model": "sonar-pro",
                "query": "original query",
                "tokens": {"prompt": N, "completion": N},
                "latency_ms": N,
            }
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        start = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        latency_ms = (time.time() - start) * 1000

        content = response.choices[0].message.content or ""

        # Perplexity returns citations as an extra field.
        # The OpenAI SDK may or may not preserve it — try multiple paths.
        citations = []
        if hasattr(response, "citations"):
            citations = response.citations or []
        elif hasattr(response, "model_extra"):
            citations = response.model_extra.get("citations", [])

        return {
            "content": content,
            "citations": citations,
            "model": self.model,
            "query": query,
            "tokens": {
                "prompt": response.usage.prompt_tokens if response.usage else 0,
                "completion": response.usage.completion_tokens if response.usage else 0,
            },
            "latency_ms": round(latency_ms),
        }
