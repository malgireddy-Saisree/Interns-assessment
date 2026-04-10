"""
ingest.py
Orchestrates the full ingestion pipeline:
  1. Load documents from Azure Blob Storage
  2. Chunk each document
  3. Embed each chunk
  4. Upload to Azure AI Search index
 
Run this script once to (re-)index all blobs, or on a schedule to keep
the index fresh.
 
Usage:
    python -m ingestion.ingest
    # or with optional filter:
    python -m ingestion.ingest --source-prefix "faqs/"
"""
from __future__ import annotations
 
import argparse
import logging
import os
import re
from typing import List
from dotenv import load_dotenv
load_dotenv()
 
from ingestion.blob_loader import BlobLoader, BlobDocument
from ingestion.chunker import RecursiveChunker, Chunk
from ingestion.embedder import AzureEmbedder
from ingestion.search_index import AzureSearchIndex
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)
 
 
# ---------------------------------------------------------------------------
# Helper: sanitise a string so it's a valid Azure Search document key
# ---------------------------------------------------------------------------
_KEY_RE = re.compile(r"[^a-zA-Z0-9_\-=]")
 
def _make_key(chunk_id: str) -> str:
    """Replace characters not allowed in Azure Search keys with underscores."""
    return _KEY_RE.sub("_", chunk_id)[:1024]  # max key length is 1024
 
 
# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
 
def run_ingestion(source_prefix: str | None = None) -> None:
    # ---- Read config from environment (12-factor style) ------------------
    blob_conn_str      = os.environ["AZURE_BLOB_CONNECTION_STRING"]
    blob_container     = os.environ["AZURE_BLOB_CONTAINER"]
    aoai_endpoint      = os.environ["AZURE_OPENAI_ENDPOINT"]
    aoai_key           = os.environ["AZURE_OPENAI_API_KEY"]
    aoai_api_version   = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
    aoai_embed_deploy  = os.environ.get("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
    search_endpoint    = os.environ["AZURE_SEARCH_ENDPOINT"]
    search_key         = os.environ["AZURE_SEARCH_API_KEY"]
    search_index       = os.environ.get("AZURE_SEARCH_INDEX_NAME", "faq-index")
 
    # ---- Initialise components -------------------------------------------
    loader  = BlobLoader(blob_conn_str, blob_container)
    chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=150)
    embedder = AzureEmbedder(
        azure_endpoint=aoai_endpoint,
        api_key=aoai_key,
        api_version=aoai_api_version,
        deployment_name=aoai_embed_deploy,
    )
    index = AzureSearchIndex(
        endpoint=search_endpoint,
        api_key=search_key,
        index_name=search_index,
    )
 
    # ---- Ensure index exists ----------------------------------------------
    index.create_or_update_index()
 
    # ---- Load & chunk all documents --------------------------------------
    all_chunks: List[Chunk] = []
    logger.info("Loading documents from blob container '%s' …", blob_container)
 
    for doc in loader.load_all():
        if source_prefix and not doc.name.startswith(source_prefix):
            continue
        chunks = chunker.chunk_document(doc)
        logger.info("  %s → %d chunks", doc.name, len(chunks))
        all_chunks.extend(chunks)
 
    if not all_chunks:
        logger.warning("No chunks produced. Nothing to index.")
        return
 
    logger.info("Total chunks to embed and index: %d", len(all_chunks))
 
    # ---- Embed all chunks (batched internally) ---------------------------
    logger.info("Embedding chunks …")
    texts   = [c.text for c in all_chunks]
    vectors = embedder.embed_texts(texts)
 
    # ---- Build documents for Azure AI Search -----------------------------
    search_docs = []
    for chunk, vector in zip(all_chunks, vectors):
        search_docs.append(
            {
                "id":             _make_key(chunk.chunk_id),
                "content":        chunk.text,
                "source":         chunk.source,
                "chunk_index":    chunk.metadata.get("chunk_index", 0),
                "chunk_count":    chunk.metadata.get("chunk_count", 1),
                "last_modified":  chunk.metadata.get("last_modified", ""),
                "content_vector": vector,
            }
        )
 
    # ---- Upload to index --------------------------------------------------
    logger.info("Uploading %d documents to Azure AI Search …", len(search_docs))
    index.upload_documents(search_docs)
    logger.info("Ingestion complete.")
 
 
# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FAQ RAG ingestion pipeline.")
    parser.add_argument(
        "--source-prefix",
        default=None,
        help="Only ingest blobs whose name starts with this prefix, e.g. 'faqs/'",
    )
    args = parser.parse_args()
    run_ingestion(source_prefix=args.source_prefix)
 