import os
DB_TABLE = os.getenv("DB_TABLE", "contacts")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*")
PORT = int(os.getenv("PORT", "8080"))
