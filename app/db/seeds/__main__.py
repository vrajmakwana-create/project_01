import asyncio
from app.db.seeds import seed_all

if __name__ == "__main__":
    asyncio.run(seed_all())

