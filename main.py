import uuid
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import redis
from log_exp_wrapper import log_async_exceptions,log_exceptions
from celery import Celery
from app.tasks import process_visit
from app.redis_store import (
    visit_redis,
    set_visit_status,
    set_visit_data,
    get_visit_status,
    set_visit_report,
    get_visit_report,
)

# Configuration (inline)
# Redis database 0 for Celery broker & backend\CELERY_REDIS_URL = os.getenv("CELERY_REDIS_URL", "redis://localhost:6379/0")
UPLOAD_DIR = os.path.abspath(os.getenv("UPLOAD_DIR", "uploads"))

# Initialize upload directory
os.makedirs(UPLOAD_DIR, exist_ok=True)

# FastAPI app
app = FastAPI()

class CreateVisitResponse(BaseModel):
    visit_id: str

@app.post("/create-visit")
def create_visit(visit_type:str):
    """
    Create a new visit and initialize its state.
    """
    visit_id = str(uuid.uuid4())
    # Initial status is 'created'
    set_visit_data(visit_id, "created",visit_type)
    return {"visit_id": visit_id}

@log_exceptions
@app.post("/upload_chunk/{visit_id}")
def upload_chunk(visit_id: str, chunk: UploadFile = File(...)):
    """
    Accept an audio chunk for transcription and trigger processing.
    """
    # Verify visit exists
    if get_visit_status(visit_id) is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    # Save uploaded audio
    file_path = os.path.join(UPLOAD_DIR, f"{visit_id}.wav")
    with open(file_path, "wb") as f:
        f.write(chunk.file.read())

    # Update status to processing
    set_visit_status(visit_id, "processing")
    # Trigger background task
    process_visit.delay(visit_id, file_path)

    return {"detail": "Upload received, processing started"}

@app.get("/status/{visit_id}")
def get_status(visit_id: str):
    """
    Retrieve the current processing status for a visit.
    """
    status = get_visit_status(visit_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    return {"visit_id": visit_id, "status": status}

@app.get("/report/{visit_id}")
def get_report(visit_id: str):
    """
    Once complete, return the generated SOAP note report.
    """
    status = get_visit_status(visit_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    if status != "complete":
        raise HTTPException(status_code=400, detail="Report not ready")

    report = get_visit_report(visit_id)
    return {"visit_id": visit_id, "report": report}