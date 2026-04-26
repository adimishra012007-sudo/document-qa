from sqlalchemy.orm import Session
from app.models.user import ProcessingJob
from app.services.pdf_service import PDFService
from app.services.rag.rag_service import RAGService
import logging

logger = logging.getLogger(__name__)
pdf_service = PDFService()
rag_service = RAGService()

async def run_ingestion_task(
    db: Session, 
    job_id: str, 
    file_path: str, 
    user_id: int, 
    document_id: str
):
    """
    Background job to process PDF and create embeddings.
    Updates the ProcessingJob record as it progresses.
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found in database.")
        return

    try:
        # 1. Update status to processing
        job.status = "processing"
        db.commit()

        # 2. Extract and chunk
        chunks = pdf_service.extract_and_chunk(file_path)

        # 3. Create vector store
        rag_service.create_vector_store(chunks, user_id, document_id)

        # 4. Completion
        job.status = "completed"
        db.commit()
    except Exception as e:
        logger.exception(f"Error in background ingestion for job {job_id}")
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
