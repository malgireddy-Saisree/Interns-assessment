"""
embedder.py
Thin wrapper around Azure OpenAI's embeddings endpoint.
Handles batching and basic retry logic.
"""
from __future__ import annotations
 
import logging
import time
from typing import List
 
from openai import AzureOpenAI, APIError, RateLimitError
 
logger = logging.getLogger(__name__)
 
 
class AzureEmbedder:
    """
    Generates embeddings using an Azure OpenAI deployment.
 
    Parameters
    ----------
    azure_endpoint : str
        e.g. "https://<your-resource>.openai.azure.com/"
    api_key : str
    api_version : str
        e.g. "2024-02-01"
    deployment_name : str
        The *deployment* name in Azure OpenAI Studio, e.g. "text-embedding-3-small"
    batch_size : int
        Number of texts to embed per API call (max 2048 for Ada/3-small).
    max_retries : int
        Number of retry attempts on rate-limit errors.
    """
 
    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        api_version: str,
        deployment_name: str = "text-embedding-3-small",
        batch_size: int = 64,
        max_retries: int = 5,
    ):
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        self.deployment = deployment_name
        self.batch_size = batch_size
        self.max_retries = max_retries
 
    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
 
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Return a list of embedding vectors, one per input text.
        Order is preserved.
        """
        all_vectors: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors = self._embed_batch_with_retry(batch)
            all_vectors.extend(vectors)
        return all_vectors
 
    def embed_query(self, text: str) -> List[float]:
        """Convenience method for a single query string."""
        return self.embed_texts([text])[0]
 
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
 
    def _embed_batch_with_retry(self, batch: List[str]) -> List[List[float]]:
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.deployment,
                )
                # Sort by index to guarantee order
                items = sorted(response.data, key=lambda d: d.index)
                return [item.embedding for item in items]
            except RateLimitError:
                if attempt == self.max_retries:
                    raise
                logger.warning(
                    "Rate limit hit (attempt %d/%d). Retrying in %.1fs …",
                    attempt,
                    self.max_retries,
                    delay,
                )
                time.sleep(delay)
                delay *= 2  # exponential back-off
            except APIError as exc:
                logger.error("Azure OpenAI API error: %s", exc)
                raise
        return []  # unreachable, keeps type-checker happy
 
 