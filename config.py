import os

CHAT_ID = os.getenv("CHAT_ID")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WATCHED_TEAMS = os.getenv("WATCHED_TEAMS", "").split(",")  # CSV to list
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
MIN_TRANSFER_VALUE = int(os.getenv("MIN_TRANSFER_VALUE", "20000000"))
