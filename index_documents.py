import os
import re
import argparse
import psycopg2
from psycopg2.extras import Json
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Configure Gemini
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=GEMINI_API_KEY)


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        return conn
    except Exception as e:
        raise ConnectionError(f"Failed to connect to DB: {e}")


def init_db():
    """Initializes the database table and vector extension if they do not exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS document_embeddings (
            id SERIAL PRIMARY KEY,
            chunk_text TEXT NOT NULL,
            embedding vector(768),
            filename TEXT NOT NULL,
            split_strategy TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"DB Initialization Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def extract_text(file_path: str) -> str:
    """Extracts clean text from PDF or DOCX files while preserving paragraph structure."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"  # Preserve paragraphs
        elif ext == '.docx':
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n\n"  # Preserve paragraphs
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Smart cleanup: remove extra spaces and tabs, keep paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max two consecutive empty lines
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from {file_path}: {e}")


def split_text(text: str, strategy: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Splits text into chunks based on the selected strategy."""
    chunks = []

    if strategy == 'fixed':
        # Fixed-size chunks with overlap
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap

    elif strategy == 'sentence':
        # Split text by sentence boundaries (.!?)
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = ""
        for sentence in raw_sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk:
            chunks.append(current_chunk.strip())

    elif strategy == 'paragraph':
        # Split by double newlines
        chunks = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        # Fallback if the document has no clear paragraphs
        if not chunks:
            return split_text(text, 'fixed', chunk_size, overlap)

    else:
        raise ValueError("Unknown strategy. Choose: fixed, sentence, paragraph")

    return [c for c in chunks if c]  # Remove empty chunks


def generate_embedding(text: str) -> List[float]:
    """Generates an embedding using the Google Gemini API."""
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding failed for chunk: {text[:30]}... Error: {e}")
        return []


def save_to_db(chunks: List[str], embeddings: List[List[float]], filename: str, strategy: str):
    """Saves text chunks and embeddings to PostgreSQL."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = """
        INSERT INTO document_embeddings (chunk_text, embedding, filename, split_strategy)
        VALUES (%s, %s, %s, %s)
        """
        saved_count = 0
        for chunk, vec in zip(chunks, embeddings):
            if vec:  # Do not save empty embeddings
                cur.execute(query, (chunk, vec, filename, strategy))
                saved_count += 1

        conn.commit()
        print(f"Successfully saved {saved_count}/{len(chunks)} chunks to DB.")
    except Exception as e:
        print(f"Database Insert Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents, split them into chunks, and store embeddings in PostgreSQL."
    )
    parser.add_argument("file_path", help="Path to the PDF or DOCX file")
    parser.add_argument(
        "--strategy",
        choices=['fixed', 'sentence', 'paragraph'],
        default='fixed',
        help="Chunking strategy"
    )

    args = parser.parse_args()

    # 1. Initialize database
    init_db()

    # 2. Extract text
    print(f"Extracting text from {args.file_path}...")
    try:
        raw_text = extract_text(args.file_path)
    except Exception as e:
        print(e)
        return

    # 3. Split text
    print(f"Splitting text using '{args.strategy}' strategy...")
    chunks = split_text(raw_text, args.strategy)
    print(f"Generated {len(chunks)} chunks.")

    # 4. Generate embeddings
    print("Generating embeddings with Gemini...")
    embeddings = []
    for chunk in chunks:
        vec = generate_embedding(chunk)
        embeddings.append(vec)

    # 5. Save to database
    print("Saving to PostgreSQL...")
    save_to_db(chunks, embeddings, os.path.basename(args.file_path), args.strategy)
    print("Process complete.")


if __name__ == "__main__":
    main()
