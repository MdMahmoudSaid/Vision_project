from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cloud_attendance.auth.dependencies import require_sync_api_key
from cloud_attendance.database import get_db
from cloud_attendance.schemas.sync import SyncBatchRequest, SyncBatchResponse
from cloud_attendance.services.sync_ingest_service import ingest_sync_batch

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/batch", response_model=SyncBatchResponse)
def sync_batch(
    payload: SyncBatchRequest,
    db: Session = Depends(get_db),
    site_id: str = Depends(require_sync_api_key),
) -> SyncBatchResponse:
    # site_id could be stored if we added it to our models, but currently we just rely on idempotency
    return ingest_sync_batch(db, payload)
