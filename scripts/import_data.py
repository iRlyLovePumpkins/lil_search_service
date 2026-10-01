import asyncio
import os
import ast
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.document import DocumentModel, Base
from app.core.elastic import es_client
from elasticsearch.helpers import async_bulk

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/search_db")
INDEX_NAME = "documents_index"
CSV_FILE_PATH = "posts.csv"

async def init_indices():
    if not await es_client.indices.exists(index=INDEX_NAME):
        await es_client.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "text": {"type": "text"}
                    }
                }
            }
        )
        print(f"Создан индекс Elasticsearch: {INDEX_NAME}")

async def import_data():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Файл {CSV_FILE_PATH} не найден.")
        return

    print("Чтение CSV-файла...")
    df = pd.read_csv(CSV_FILE_PATH)
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await init_indices()

    print(f"Импорт {len(df)} записей...")

    async with AsyncSessionLocal() as session:
        es_actions = []
        
        for index, row in df.iterrows():
            doc_id = str(index + 1)
            
            text = str(row["text"])
            created_date = pd.to_datetime(row["created_date"])
            rubrics_raw = row["rubrics"]

            if isinstance(rubrics_raw, str):
                try:
                    rubrics = ast.literal_eval(rubrics_raw)
                except Exception:
                    rubrics = []
            else:
                rubrics = []

            existing = await session.get(DocumentModel, doc_id)
            if not existing:
                new_doc = DocumentModel(
                    id=doc_id,
                    rubrics=rubrics,
                    text=text,
                    created_date=created_date
                )
                session.add(new_doc)

            es_actions.append({
                "_index": INDEX_NAME,
                "_id": doc_id,
                "_source": {
                    "id": doc_id,
                    "text": text
                }
            })

        await session.commit()
        
        if es_actions:
            await async_bulk(es_client, es_actions)

    print("Импорт успешно завершен.")

if __name__ == "__main__":
    asyncio.run(import_data())