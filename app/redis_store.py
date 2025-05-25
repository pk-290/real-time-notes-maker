import os
import redis
from log_exp_wrapper import log_exceptions

# Redis URL for storing visit data (status & reports)
VISIT_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")

# Initialize Redis client
visit_redis = redis.Redis.from_url(VISIT_REDIS_URL)


def set_visit_status(visit_id: str, status: str) -> None:
    """
    Update the status of a visit.
    """
    visit_redis.hset(f"visit:{visit_id}", "status", status)

def set_visit_type(visit_id: str, status: str, visit_type: str) -> None:
    visit_redis.hset(f"visit:{visit_id}", mapping={
        "status": status,
        "type_of_visit": visit_type
    })


def get_visit_status(visit_id: str) -> str:
    """
    Retrieve the status of a visit.
    """
    value = visit_redis.hget(f"visit:{visit_id}", "status")
    return value.decode() if value else None

@log_exceptions
def set_chunk_report(visit_id: str,chunk_number:int, report,is_final=False) -> None:
    """
    Save the generated report for a visit.
    """
    print(report)
    if is_final:
        visit_redis.hset(f"visit:{visit_id}", mapping={"report": str(report), "status": "completed"})
    visit_redis.hset(f"visit:{visit_id}", mapping={"report": str(report), "status": f"Processed chunk number: {chunk_number} completed"})



def get_visit_report(visit_id: str) -> str:
    """
    Retrieve the generated report for a visit.
    """
    data = visit_redis.hgetall(f"visit:{visit_id}")
    return data.get(b"report").decode() if data.get(b"report") else None