"""
Search for hotel information and FAQs.
Drop-in replacement for the original faq_search_tool.py.
 
At query time this module:
  1. Embeds the user's question with Azure OpenAI.
  2. Runs a hybrid search (BM25 + vector) against Azure AI Search.
  3. Assembles the top-k chunks into a context string.
  4. Returns a grounded answer string ready for the planner to use.
"""
from __future__ import annotations
 
import logging
import os
from typing import List, Optional

from langchain_core.tools import tool

try:
    from ingestion.embedder import AzureEmbedder
    from ingestion.search_index import AzureSearchIndex
except ImportError:
    # Fallback to handle typo in folder name if it exists
    from ingesion.embedder import AzureEmbedder
    from ingesion.search_index import AzureSearchIndex

logger = logging.getLogger(__name__)

class FAQRetriever:
    """
    Retrieves the most relevant FAQ chunks for a given question.
    Instantiate once and reuse (embedder & search clients are persistent).
    """

    def __init__(
        self,
        top_k: int = 5,
        source_filter: Optional[str] = None,
    ):
        aoai_endpoint    = os.environ["AZURE_OPENAI_ENDPOINT"]
        aoai_key         = os.environ["AZURE_OPENAI_API_KEY"]
        aoai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
        aoai_embed_deploy = os.environ.get("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
        search_endpoint  = os.environ["AZURE_SEARCH_ENDPOINT"]
        search_key       = os.environ["AZURE_SEARCH_API_KEY"]
        search_index     = os.environ.get("AZURE_SEARCH_INDEX_NAME", "faq-index")
 
        self.embedder = AzureEmbedder(
            azure_endpoint=aoai_endpoint,
            api_key=aoai_key,
            api_version=aoai_api_version,
            deployment_name=aoai_embed_deploy,
        )
        self.index = AzureSearchIndex(
            endpoint=search_endpoint,
            api_key=search_key,
            index_name=search_index,
        )
        self.top_k = top_k
        self.source_filter = source_filter  # e.g. "source eq 'faqs/policy.pdf'"
 
    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
 
    def retrieve(self, question: str) -> List[dict]:
        """
        Return a list of the top-k matching chunk dicts:
            [{"id", "content", "source", "chunk_index", "score"}, ...]
        """
        query_vector = self.embedder.embed_query(question)
        hits = self.index.hybrid_search(
            query_text=question,
            query_vector=query_vector,
            top_k=self.top_k,
            filter_expr=self.source_filter,
        )
        return hits
 
    def retrieve_as_context(self, question: str) -> str:
        """
        Return retrieved chunks formatted as a context string for the LLM.
        """
        hits = self.retrieve(question)
        if not hits:
            return "No relevant FAQ content found."
 
        parts: List[str] = []
        for i, hit in enumerate(hits, start=1):
            parts.append(
                f"[{i}] Source: {hit['source']} (chunk {hit['chunk_index']})\n"
                f"{hit['content'].strip()}"
            )
        return "\n\n---\n\n".join(parts)
 
 
# ---------------------------------------------------------------------------
# Module-level singleton (lazy-initialised on first call)
# ---------------------------------------------------------------------------
_retriever: Optional[FAQRetriever] = None
 
 
def _get_retriever() -> FAQRetriever:
    global _retriever
    if _retriever is None:
        _retriever = FAQRetriever()
    return _retriever
 
 
# ---------------------------------------------------------------------------
# Public helper — same signature as the original get_faq_answer
# ---------------------------------------------------------------------------
 
def get_faq_answer(question: str) -> str:
    """
    Retrieve the most relevant FAQ context for *question* and return it as
    a formatted string.  The planner's LLM will synthesise a final answer
    from this context.
    """
    retriever = _get_retriever()
    context = retriever.retrieve_as_context(question)
    logger.debug("Retrieved context for question '%s':\n%s", question, context)
    return context
 
 
@tool
def faq_search_tool(question: str) -> str:
    """Search the hotel knowledge base for FAQs, policies, room info, services, and general hotel questions.
    Args:
        question: The user's question about the hotel, policies, rooms, or services.
    Returns a grounded answer from the document knowledge base.
    """
    return get_faq_answer(question)
