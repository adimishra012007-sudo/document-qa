from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.user import ProcessingJob
from app.services.pdf_service import PDFService
from app.services.rag.rag_service import RAGService
import logging
import time

logger = logging.getLogger(__name__)
pdf_service = PDFService()
rag_service = RAGService()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, job_id: str, file_path: str, user_id: int, document_id: str):
    """
    Celery task to handle the compute-heavy RAG pipeline.
    """
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found.")
            return

        job.status = "processing"
        db.commit()

        # RAG Pipeline execution
        logger.info(f"Starting ingestion for file: {file_path}")
        chunks = pdf_service.extract_and_chunk(file_path)
        rag_service.index_documents(chunks, user_id, document_id)

        job.status = "completed"
        db.commit()
        logger.info(f"Successfully completed job: {job_id}")
        
    except Exception as e:
        logger.exception(f"Error processing document {document_id}")
        
        # Retry logic for transient errors
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            job.status = "failed"
            job.error_message = f"Max retries exceeded: {str(e)}"
            db.commit()
    finally:
        db.close()
