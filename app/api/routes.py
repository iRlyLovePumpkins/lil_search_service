from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.document import DocumentResponse
from app.services.search import SearchService

router = APIRouter()

@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(query: str, db: AsyncSession = Depends(get_db)):
    return await SearchService.search_documents(query, db)

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    await SearchService.delete_document(doc_id, db)
    return None