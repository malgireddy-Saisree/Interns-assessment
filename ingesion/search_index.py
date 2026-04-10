"""
search_index.py
Creates (or updates) an Azure AI Search index with a vector field,
and provides helpers to upload documents and run hybrid searches.
"""
from __future__ import annotations
 
import logging
from typing import Any, Dict, List, Optional
 
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
 
logger = logging.getLogger(__name__)
 
# Dimension must match your embedding model:
#   text-embedding-ada-002  → 1536
#   text-embedding-3-small  → 1536
#   text-embedding-3-large  → 3072
VECTOR_DIMENSIONS = 1536
 
 
class AzureSearchIndex:
    """
    Wraps Azure AI Search index creation, document upload, and retrieval.
 
    Parameters
    ----------
    endpoint : str
        e.g. "https://<your-service>.search.windows.net"
    api_key : str
        Admin key for index management; query key is sufficient for search.
    index_name : str
        Name of the search index to create / use.
    vector_dimensions : int
        Must match the output size of your embedding model.
    """
 
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        vector_dimensions: int = VECTOR_DIMENSIONS,
    ):
        credential = AzureKeyCredential(api_key)
        self.index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
        self.search_client = SearchClient(
            endpoint=endpoint, index_name=index_name, credential=credential
        )
        self.index_name = index_name
        self.vector_dimensions = vector_dimensions
 
    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------
 
    def create_or_update_index(self) -> None:
        """
        Create the index if it doesn't exist, or update it if the schema
        has changed.  Safe to call on every ingestion run.
        """
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name="en.microsoft",
            ),
            SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="chunk_count", type=SearchFieldDataType.Int32),
            SimpleField(name="last_modified", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self.vector_dimensions,
                vector_search_profile_name="hnsw-profile",
            ),
        ]
 
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")],
        )
 
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
        )
 
        self.index_client.create_or_update_index(index)
        logger.info("Index '%s' ready.", self.index_name)
 
    # ------------------------------------------------------------------
    # Document upload
    # ------------------------------------------------------------------
 
    def upload_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """
        Upload (upsert) documents to the index in batches.
 
        Each document dict must contain at minimum:
            id, content, source, chunk_index, chunk_count, content_vector
        """
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            result = self.search_client.upload_documents(documents=batch)
            failed = [r for r in result if not r.succeeded]
            if failed:
                for f in failed:
                    logger.error("Failed to index doc %s: %s", f.key, f.error_message)
            logger.info(
                "Uploaded batch %d–%d (%d docs).",
                i,
                i + len(batch),
                len(batch),
            )
 
    # ------------------------------------------------------------------
    # Search / retrieval
    # ------------------------------------------------------------------
 
    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform a hybrid search combining BM25 keyword search with
        vector similarity (HNSW).  Returns up to *top_k* results.
 
        Parameters
        ----------
        query_text : str
            Raw query for the full-text (BM25) part.
        query_vector : list[float]
            Embedded query vector for the ANN part.
        top_k : int
            Number of results to return.
        filter_expr : str, optional
            OData filter string, e.g. "source eq 'policy.pdf'"
        """
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )
 
        results = self.search_client.search(
            search_text=query_text,
            vector_queries=[vector_query],
            select=["id", "content", "source", "chunk_index"],
            filter=filter_expr,
            top=top_k,
        )
 
        hits = []
        for r in results:
            hits.append(
                {
                    "id": r["id"],
                    "content": r["content"],
                    "source": r["source"],
                    "chunk_index": r.get("chunk_index"),
                    "score": r["@search.score"],
                }
            )
        return hits
 
 