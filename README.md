# 📄 AI Document Vectorizer & Indexer

A production-ready Python utility that ingests PDF/DOCX documents, intelligently chunks their content, generates semantic embeddings using **Google Gemini**, and stores them in a **PostgreSQL database with pgvector** support.

This project was built as part of an academic assignment and fully complies with all functional and security requirements.

---

## 🚀 Key Features

- **Multi-Format Support**  
  Native support for `.pdf` and `.docx` documents.

- **Smart Chunking (3 Strategies)**  
  - `fixed` – Fixed-size chunks with overlap  
  - `sentence` – Sentence-based splitting using punctuation  
  - `paragraph` – Paragraph-based splitting (structure-preserving)

- **Gemini-Powered Embeddings**  
  Uses Google Gemini `embedding-001` API to generate high-quality vector embeddings.

- **Vector Database**  
  Stores text chunks and embeddings in **PostgreSQL + pgvector**.

- **Docker Ready**  
  Includes a pre-configured Docker Compose setup for PostgreSQL with pgvector enabled.

- **Secure by Design**  
  No credentials are hardcoded – all secrets are managed via environment variables.

---

## 🛠️ Setup & Installation
```bash
### 1. Clone the Repository

git clone https://github.com/your-username/ai-document-vectorizer.git
cd ai-document-vectorizer


### 2. Environment Setup
Create a .env file in the root directory:

GEMINI_API_KEY=your_api_key_here
POSTGRES_URL=postgresql://myuser:mypassword@localhost:5432/vectordb

⚠️ Never commit the .env file – it is excluded via .gitignore.

### 3. Start the Database (Docker) 🐳
docker-compose up -d

This starts a PostgreSQL container with the pgvector extension enabled and ready for use.

### 4. Install Dependencies
pip install -r requirements.txt

Usage

Run the script from the command line:

python index_documents.py <file_path> --strategy <strategy_name>

Example:
python index_documents.py "./docs/resume.pdf" --strategy paragraph
```


## Chunking Strategies
```bash
Strategy      |   Description	                          |     Best For

fixed	      |   Fixed size (500 chars) with overlap	  |     General purpose raw data
sentence	  |   Splits by sentence boundaries (.!?)	  |     Context-aware NLP tasks
paragraph	  |   Preserves structure (\n\n) (Recommended)|	Legal contracts, articles, and resumes
```

## Database Schema
The script automatically initializes the following table:
```bash

Column	       |     Type	      |  Description

id	           |     SERIAL	      |  Primary Key
chunk_text	   |     TEXT	      |  The extracted text segment
embedding	   |     vector(768)  |	 The Gemini vector
filename	   |     TEXT	      |  Original file name
split_strategy |	    TEXT	  |  Method used for splitting
created_at	   |     TIMESTAMP	  |  Automatic insertion timestamp
```
## Security & Best Practices

Environment Variables
API keys and DB credentials are stored securely using .env.

Input Validation
Supports only valid PDF/DOCX files.

Clean Text Extraction
Normalizes and cleans extracted text before chunking.

Modular & Documented Code
Clear separation of concerns for extraction, chunking, embedding, and persistence.

## Assignment Compliance

This project fulfills all assignment requirements:

✔️ PDF and DOCX ingestion

✔️ Clean text extraction

✔️ Three chunking strategies (fixed, sentence, paragraph)

✔️ Embedding generation using Google Gemini API

✔️ PostgreSQL storage with pgvector

✔️ Secure configuration using environment variables

✔️ Clean, modular, and documented Python code

## Author
Yuval Snegur
Computer Science Graduate
AI & Full-Stack Engineering





