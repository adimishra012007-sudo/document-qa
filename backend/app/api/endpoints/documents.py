import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.schemas import ProcessResponse, QueryRequest, QueryResponse, JobStatus
from app.services.pdf_service import PDFService
from app.services.rag.rag_service import RAGService
from app.worker.tasks import process_document_task
from app.core.config import settings
from app.core import security
from app.api import deps
from app.models.user import User, ProcessingJob, ChatSession, ChatMessage
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()
pdf_service = PDFService()
rag_service = RAGService()

@router.post("/upload", response_model=ProcessResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    document_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    
    # Store uploads in user-specific folder
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    file_path = os.path.join(user_upload_dir, f"{document_id}.pdf")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create a job record in DB
    new_job = ProcessingJob(
        id=job_id,
        user_id=current_user.id,
        document_id=document_id,
        status="pending"
    )
    db.add(new_job)
    db.commit()

    # Trigger Celery background task
    process_document_task.delay(
        job_id, 
        file_path, 
        current_user.id, 
        document_id
    )
    
    return ProcessResponse(
        document_id=document_id,
        message=f"Upload successful. Job {job_id} started.",
        status="pending"
    )

@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id,
        ProcessingJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    return JobStatus(
        job_id=job.id,
        document_id=job.document_id,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.post("/query", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. Manage Session
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            new_session = ChatSession(
                id=session_id, 
                user_id=current_user.id, 
                document_id=request.document_id
            )
            db.add(new_session)
            db.commit()
        
        # 2. Get chat history for this session
        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        formatted_history = [
            {"role": msg.role, "content": msg.content} for msg in history
        ]

        # 3. Get answer from RAG
        result = await rag_service.get_answer(
            request.query, 
            current_user.id, 
            request.document_id,
            chat_history=formatted_history
        )

        # 4. Save User Message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.query
        )
        db.add(user_msg)

        # 5. Save AI Message
        bot_msg = ChatMessage(
            session_id=session_id,
            role="bot",
            content=result["answer"],
            sources=result["sources"]
        )
        db.add(bot_msg)
        db.commit()

        return QueryResponse(session_id=session_id, **result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
