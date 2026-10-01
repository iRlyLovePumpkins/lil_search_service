from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from elasticsearch import NotFoundError

from app.models.document import DocumentModel
from app.core.elastic import es_client

INDEX_NAME = "documents_index"

class SearchService:

    @staticmethod
    async def search_documents(query: str, db: AsyncSession) -> list[DocumentModel]:
        es_response = await es_client.search(
            index=INDEX_NAME,
            query={"match": {"text": query}},
            size=100
        )
        doc_ids = [hit["_source"]["id"] for hit in es_response["hits"]["hits"]]
        
        if not doc_ids:
            return []

        stmt = (
            select(DocumentModel)
            .where(DocumentModel.id.in_(doc_ids))
            .order_by(DocumentModel.created_date.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_document(doc_id: str, db: AsyncSession) -> None:
        db_doc = await db.get(DocumentModel, doc_id)
        if not db_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
        await db.delete(db_doc)
        await db.commit()
        try:
            await es_client.delete(index=INDEX_NAME, id=doc_id)
        except NotFoundError:
            pass