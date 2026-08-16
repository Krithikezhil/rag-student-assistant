import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
conn.commit()

print("pgvector extension enabled successfully!")

cur.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        source_file TEXT,
        embedding VECTOR(768)
    );
""")
conn.commit()

print("document_chunks table created successfully!")

cur.close()
conn.close()