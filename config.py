import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "6302553503").split(",")]
