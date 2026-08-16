import os
import psycopg2
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# Allow the React frontend to call this backend (same pattern as Project 1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # we'll tighten this to the real frontend URL once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str

def get_query_embedding(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
        output_dimensionality=768
    )
    return result["embedding"]

def find_similar_chunks(question_embedding, top_k=3):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT content, source_file, embedding <=> %s::vector AS distance
        FROM document_chunks
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (question_embedding, top_k)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{"content": r[0], "source_file": r[1], "distance": r[2]} for r in results]

def generate_answer(question, context_chunks):
    # Only treat chunks as "relevant" if they're reasonably close in meaning.
    # Cosine distance ranges 0 (identical) to 2 (opposite); 0.5 is a practical cutoff.
    relevant_chunks = [c for c in context_chunks if c["distance"] < 0.5]

    model = genai.GenerativeModel("gemini-flash-latest")

    if relevant_chunks:
        context_text = "\n\n".join([f"[From {c['source_file']}]: {c['content']}" for c in relevant_chunks])
        prompt = f"""You are a helpful study assistant. Answer the question using the context below if it's relevant.
If the context doesn't fully cover the question, you may also use your own general academic knowledge to complete the answer,
but prioritize and clearly ground your answer in the context when it applies.

Context:
{context_text}

Question: {question}

Answer:"""
        response = model.generate_content(prompt)
        return response.text, [c["source_file"] for c in relevant_chunks]
    else:
        # Nothing relevant in the notes -- fall back to general academic knowledge
        prompt = f"""You are a helpful academic study assistant. Answer the following question clearly and accurately,
as you would for a student studying any subject.

Question: {question}

Answer:"""
        response = model.generate_content(prompt)
        return response.text, []

@app.get("/")
def read_root():
    return {"status": "RAG Student Assistant backend is running"}

@app.post("/api/ask")
def ask_question(request: AskRequest):
    question_embedding = get_query_embedding(request.question)
    similar_chunks = find_similar_chunks(question_embedding)
    answer, sources = generate_answer(request.question, similar_chunks)

    return {
        "answer": answer,
        "sources": sources
    }