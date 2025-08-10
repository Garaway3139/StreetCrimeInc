import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data.db")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
