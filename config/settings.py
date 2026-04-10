"""
Loads environment variables from .env and exports typed constants
used throughout the application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ── Azure OpenAI ──────────────────────────────────────────────
AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# ── Database ──────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", str(Path(__file__).resolve().parent.parent / "stayease.db"))

# ── Memory ────────────────────────────────────────────────────
CONVERSATION_WINDOW_SIZE: int = int(os.getenv("CONVERSATION_WINDOW_SIZE", "10"))
