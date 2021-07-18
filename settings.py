import os


DB_URL = os.environ.get("DB_URL", "sqlite:///./sql_app.db")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
