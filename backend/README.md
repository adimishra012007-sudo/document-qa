# AI Document QA - Backend (Phase 1)

Modular FastAPI backend for document question answering using RAG.

## Features
- **PDF Upload**: Extracts text and page metadata.
- **Auto-indexing**: Chunking and FAISS vector store creation.
- **Natural Language QA**: Retrieval-Augmented Generation using OpenAI.
- **Source Referencing**: Provides page numbers for every answer.

## Tech Stack
- **FastAPI**: API framework.
- **LangChain**: RAG orchestration.
- **FAISS**: Local vector database.
- **OpenAI**: LLM and Embeddings.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Rename `.env.example` to `.env`.
   - Add your `OPENAI_API_KEY`.

3. **Run the Server**:
   ```bash
   python -m app.main
   ```

## API Endpoints
- `POST /api/v1/documents/upload`: Upload and index a PDF.
- `POST /api/v1/documents/query`: Ask a question about an indexed document.

## Future Upgrades (Phase 2+)
- [ ] JWT Authentication
- [ ] Multi-user isolation (Namespaces)
- [ ] Celery for background processing
- [ ] Cloud Vector DB (Pinecone)
