import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*50)
print("   Azure Connection Checker")
print("="*50)


# ── 1. Check .env values are loaded ──────────────────────────────────────────
print("\n📋 Step 1: Checking .env values...")

keys = {
    "AZURE_OPENAI_API_KEY":             os.getenv("AZURE_OPENAI_API_KEY"),
    "AZURE_OPENAI_ENDPOINT":            os.getenv("AZURE_OPENAI_ENDPOINT"),
    "AZURE_OPENAI_CHAT_DEPLOYMENT":     os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT":os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    "AZURE_SEARCH_ENDPOINT":            os.getenv("AZURE_SEARCH_ENDPOINT"),
    "AZURE_SEARCH_KEY":                 os.getenv("AZURE_SEARCH_KEY"),
    "AZURE_SEARCH_INDEX":               os.getenv("AZURE_SEARCH_INDEX"),
    "BLOB_CONNECTION_STRING":           os.getenv("BLOB_CONNECTION_STRING"),
}

all_ok = True
for key, val in keys.items():
    if val:
        print(f"  ✅ {key} = {val[:40]}...")
    else:
        print(f"  ❌ {key} = NOT FOUND")
        all_ok = False

if not all_ok:
    print("\n⚠️  Some keys are missing. Fix your .env file first.\n")
    exit(1)


# ── 2. Check Azure OpenAI ─────────────────────────────────────────────────────
print("\n🤖 Step 2: Testing Azure OpenAI (chat)...")
try:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version="2024-02-01"
    )
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[{"role": "user", "content": "Say hello in 3 words"}],
        max_tokens=10
    )
    print(f"  ✅ Chat works! Response: {response.choices[0].message.content.strip()}")
except Exception as e:
    print(f"  ❌ Chat failed: {e}")


# ── 3. Check Azure OpenAI Embeddings ─────────────────────────────────────────
print("\n🔢 Step 3: Testing Azure OpenAI (embeddings)...")
try:
    emb = client.embeddings.create(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        input="test"
    )
    dims = len(emb.data[0].embedding)
    print(f"  ✅ Embeddings work! Vector size: {dims}")
except Exception as e:
    print(f"  ❌ Embeddings failed: {e}")


# ── 4. Check Azure AI Search ──────────────────────────────────────────────────
print("\n🔍 Step 4: Testing Azure AI Search...")
try:
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential

    idx_client = SearchIndexClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
    )
    indexes = list(idx_client.list_index_names())
    if indexes:
        print(f"  ✅ AI Search works! Found indexes: {indexes}")
    else:
        print(f"  ✅ AI Search works! No indexes yet (run rag.py index first)")
except Exception as e:
    print(f"  ❌ AI Search failed: {e}")


# ── 5. Check Blob Storage ─────────────────────────────────────────────────────
print("\n📦 Step 5: Testing Azure Blob Storage...")
try:
    from azure.storage.blob import BlobServiceClient

    blob_service = BlobServiceClient.from_connection_string(os.getenv("BLOB_CONNECTION_STRING"))
    containers = [c["name"] for c in blob_service.list_containers()]
    if containers:
        print(f"  ✅ Blob Storage works! Containers: {containers}")
    else:
        print(f"  ✅ Blob Storage works! No containers yet")
except Exception as e:
    print(f"  ❌ Blob Storage failed: {e}")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("   Done! Fix any ❌ above before running rag.py")
print("="*50 + "\n")