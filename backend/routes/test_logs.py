# backend/routes/test_logs.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import List

from backend.models.test_log_model import TestLog
from backend.services.test_log_service import get_test_logs
from backend.dependencies.auth import require_role

router = APIRouter()


@router.get("/admin/test-history", response_model=List[TestLog])
def test_history(current_user=Depends(require_role(["admin"]))):
    return get_test_logs()