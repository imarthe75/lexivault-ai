# backend/create_extension_pgvector.py
import os
import time
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

def create_extension_pgvector():
    """Attempts to connect to the database and create the pgvector extension."""
    engine = None
    for i in range(10):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("pgvector extension created successfully.")
            break
        except Exception as e:
            print(f"Attempt {i+1}/10 failed to create pgvector extension: {e}")
            time.sleep(5)
    if engine:
        engine.dispose()

if __name__ == '__main__':
    create_extension_pgvector()