from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import aioredis as redis
from aioredis import Redis
from aioredis.exceptions import RedisError
from src.backend.core.config import settings
from src.backend.core.utils.date import date_time


@asynccontextmanager
async def get_redis_client() -> AsyncGenerator[Redis, Any]:
    client = None
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            encoding="UTF-8",
            decode_responses=True,
        )
        yield client
    except RedisError as e:
        raise Exception(
            f"{date_time()}.Failing of creating redis client - {str(e)}",
        )
    finally:
        if client:
            await client.close()
