"""
Azure Cosmos DB client for StayEase Memory.
Handles initialization and provides access to the memory container.
"""
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from config.settings import (
    COSMOS_ENDPOINT,
    COSMOS_KEY,
    COSMOS_DATABASE_NAME,
    COSMOS_CONTAINER_NAME,
)

# ── Client Initialization ─────────────────────────────────────

_client = None
_database = None
_container = None

def get_container():
    """
    Initialize (if needed) and return the Cosmos DB container for memory.
    Ensures database and container exist.
    """
    global _client, _database, _container
    
    if _container:
        return _container

    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        raise ValueError("Cosmos DB credentials missing from environment.")

    _client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    
    # Ensure database exists
    _database = _client.create_database_if_not_exists(id=COSMOS_DATABASE_NAME)
    
    # The container already exists with partition key /customerId
    _container = _database.create_container_if_not_exists(
        id=COSMOS_CONTAINER_NAME,
        partition_key=PartitionKey(path="/customerId"),
        offer_throughput=400
    )
    
    return _container

def get_memory_document(conversation_id: str) -> dict:
    """Fetch the memory document for a conversation."""
    container = get_container()
    try:
        doc = container.read_item(item=conversation_id, partition_key=conversation_id)
        return doc
    except exceptions.CosmosResourceNotFoundError:
        return {"id": conversation_id, "customerId": conversation_id, "session": {}, "history": []}

def save_memory_document(doc: dict) -> None:
    """Upsert the memory document."""
    container = get_container()
    container.upsert_item(doc)
    
