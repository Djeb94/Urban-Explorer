from dotenv import load_dotenv
import os

load_dotenv()

from sqlalchemy import create_engine, text

try:
    engine = create_engine(os.getenv("POSTGRES_URL"))
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ PostgreSQL connecté")
except Exception as e:
    print(f"❌ PostgreSQL erreur : {e}")

from pymongo import MongoClient

try:
    client = MongoClient(os.getenv("MONGO_URL"), serverSelectionTimeoutMS=5000)
    client.server_info()
    print("✅ MongoDB connecté")
except Exception as e:
    print(f"❌ MongoDB erreur : {e}")