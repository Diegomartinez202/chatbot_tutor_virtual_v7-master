from fastapi import APIRouter, Depends
from typing import List
from models.test_log_model import TestLog
from services.test_log_service import get_test_logs
from dependencies.auth import require_role

router = APIRouter()

@router.get("/admin/test-history", response_model=List[TestLog])
def test_history(current_user=Depends(require_role(["admin"]))):
    return get_test_logs()
