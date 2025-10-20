from pydantic import BaseModel
from datetime import datetime

class TestLog(BaseModel):
    timestamp: datetime
    test_name: str
    result: str
    success: bool
