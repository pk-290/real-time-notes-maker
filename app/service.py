import uuid
from fastapi import HTTPException
from log_exp_wrapper import log_exceptions
from app.tasks import process_chunk
from app.redis_store import (
    set_visit_status,
    set_visit_type,
    get_visit_status,
    set_chunk_report,
    get_visit_report
)

@log_exceptions
def create_visit(visit_type:str):
    """
    Create a new visit and initialize its state.
    """
    visit_id = str(uuid.uuid4())
    # Initial status is 'created'
    set_visit_type(visit_id, "created",visit_type)
    return visit_id

@log_exceptions
def upload_chunk(visit_id: str,chunk_number:int, chunk_filepath:str,is_final=False):
    """
    Accept an audio chunk for transcription and trigger processing.
    """
    # Verify visit exists
    if get_visit_status(visit_id) is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    set_visit_status(visit_id, f"processing chunk:{chunk_number}")
    print(f"process_chunk is: {process_chunk}")
    process_chunk.delay(visit_id,chunk_number ,chunk_filepath,is_final)


@log_exceptions
def get_status(visit_id: str):
    """
    Retrieve the current processing status for a visit.
    """
    status = get_visit_status(visit_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    return {"visit_id": visit_id, "status": status}

@log_exceptions
def get_report(visit_id: str):
    """
    Once complete, return the generated SOAP note report.
    """
    status = get_visit_status(visit_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    report = get_visit_report(visit_id)
    return {"visit_id": visit_id, "report": report}


