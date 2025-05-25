import os
from celery import Celery
from app.redis_store import set_chunk_report,set_visit_status,get_visit_report
from log_exp_wrapper import log_exceptions
from app.agent import generate_clinical_report


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379')
CELERY_BACKEND_URL = os.environ.get('CELERY_BACKEND_URL','redis://localhost:6379')

# Initialize Celery
celery_app = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)

if os.name == 'nt':  # Windows
    celery_app.conf.update(
        broker_connection_retry_on_startup=True,
        worker_pool_restarts=True,
        worker_cancel_long_running_tasks_on_connection_loss=True,
    )


@celery_app.task(
    name="process_chunk",
    autoretry_for=(Exception,),  # Retry on any exception
    retry_kwargs={"max_retries": 3, "countdown": 60},  # Retry up to 5 times with 60s delay
    retry_backoff=True,  # Exponential backoff
    retry_jitter=True,  # Add random jitter to retry delay
    soft_time_limit=300  # Optional: soft time limit for task execution
)
def process_chunk(visit_id: str,chunk_number:int, audio_path: str,is_final = False):
    """
    Celery task: transcribe audio and generate SOAP note.
    """
    try:
        prev_report  = get_visit_report(visit_id)
        soap_note = generate_clinical_report(visit_id,audio_path,prev_report)
        set_chunk_report(visit_id,chunk_number, soap_note,is_final)
    except Exception as e:
        set_visit_status(visit_id,"Failed...")
        raise e
    




