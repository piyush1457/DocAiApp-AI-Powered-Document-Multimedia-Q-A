import asyncio
import uuid
import sys
import logging

logging.basicConfig(level=logging.INFO)

from app.db.base import async_session
from app.services.ingestion_service import IngestionService

async def main(file_id_str):
    file_id = uuid.UUID(file_id_str)
    print(f"Testing ingestion for {file_id}")
    async with async_session() as session:
        service = IngestionService(session)
        try:
            await service.process_file(file_id)
            print("Success")
        except Exception as e:
            print(f"Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
