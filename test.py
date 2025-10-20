from models import User
from database import AsyncSessionLocal
import asyncio

async def mock():
    async with AsyncSessionLocal() as db:
        user1 = User(
            email = "alice@example.com", 
            balance = 1489.21, 
            phone = '+1 353 3453 2345', 
            currency = 'USD', 
            full_name = 'Alice Claudia', 
        )
        user2 = User(
            email = "bob@example.com", 
            balance = 964569.66, 
            phone = '+1 253 7253 2995', 
            currency = 'USD', 
            full_name = 'Bob Claude', 
        )
        db.add_all([user1, user2])
        await db.commit()

if __name__ == "__main__":
    asyncio.run(mock())