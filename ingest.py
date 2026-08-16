import os
import psycopg2
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

def chunk_text(text, source_file):
    # Split on blank lines -- each paragraph becomes one chunk
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return [{"content": p, "source_file": source_file} for p in paragraphs]

def get_embedding(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document",
        output_dimensionality=768
    )
    return result["embedding"]

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    documents_folder = "documents"
    all_chunks = []

    for filename in os.listdir(documents_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(documents_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = chunk_text(text, filename)
            all_chunks.extend(chunks)

    print(f"Found {len(all_chunks)} chunks to embed.")

    for chunk in all_chunks:
        embedding = get_embedding(chunk["content"])
        cur.execute(
            "INSERT INTO document_chunks (content, source_file, embedding) VALUES (%s, %s, %s)",
            (chunk["content"], chunk["source_file"], embedding)
        )
        print(f"Inserted chunk from {chunk['source_file']}: {chunk['content'][:50]}...")

    conn.commit()
    cur.close()
    conn.close()
    print("Ingestion complete!")

if __name__ == "__main__":
    main()