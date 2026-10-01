from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: str
    rubrics: List[str]
    text: str
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)

class SearchResponse(BaseModel):
    total: int
    results: List[DocumentResponse]