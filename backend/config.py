"""
Central config for the FlagRegistry monitoring backend.
All values come from environment variables, see .env.example in the repo root.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent

# --- Chain / contract ---
ARBITRUM_SEPOLIA_RPC_URL = os.getenv(
    "ARBITRUM_SEPOLIA_RPC_URL", "https://sepolia-rollup.arbitrum.io/rpc"
)
FLAG_REGISTRY_ADDRESS = os.getenv("FLAG_REGISTRY_ADDRESS", "")
BACKEND_PRIVATE_KEY = os.getenv("BACKEND_PRIVATE_KEY", "")  # wallet that pays gas to call flag()

with open(BACKEND_DIR / "abi" / "FlagRegistry.json") as f:
    FLAG_REGISTRY_ABI = json.load(f)

# --- Monitoring ---
# Comma-separated list of addresses to watch, e.g. "0xabc...,0xdef..."
WATCHED_ADDRESSES = [
    a.strip() for a in os.getenv("WATCHED_ADDRESSES", "").split(",") if a.strip()
]
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))

# Flag if a single outgoing tx moves more than this fraction of the
# wallet's balance (measured right before the tx). 0.5 = 50%.
LARGE_OUTFLOW_THRESHOLD = float(os.getenv("LARGE_OUTFLOW_THRESHOLD", "0.5"))

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")  # where automatic alerts get posted
