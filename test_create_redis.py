import asyncio

from backend.services.cache.redis_client import create_redis_client


async def test():
    print("STARTING REDIS CLIENT TEST")

    client = await create_redis_client()

    print("CLIENT IS NONE:", client is None)
    print("CLIENT TYPE:", type(client).__name__ if client else "None")

    if client is not None:
        print("CLIENT PING:", await client.ping())
        await client.aclose()


asyncio.run(test())