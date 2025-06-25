import logging
import os
from typing import Optional # Importar Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, redis_url: Optional[str] = None):
        self._redis_url = redis_url if redis_url else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis_client: Optional[redis.Redis] = None
        logger.info(f"RedisCache initialized with URL: {self._redis_url}")

    async def initialize(self):
        """Initializes the Redis client."""
        try:
            self._redis_client = redis.from_url(self._redis_url, decode_responses=True)
            logger.info("Redis client created.")
        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            self._redis_client = None # Ensure client is None on failure

    async def ping(self) -> bool:
        """Pings the Redis server to check connectivity."""
        if not self._redis_client:
            logger.warning("Redis client not initialized. Cannot ping.")
            return False
        try:
            await self._redis_client.ping()
            logger.info("Redis ping successful.")
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def close(self):
        """Closes the Redis client connection."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis client closed.")

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """Sets a key-value pair in Redis."""
        if not self._redis_client:
            logger.warning("Redis client not initialized. Cannot set key.")
            return
        try:
            await self._redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Failed to set key '{key}' in Redis: {e}")

    async def get(self, key: str) -> Optional[str]:
        """Gets a value from Redis by key."""
        if not self._redis_client:
            logger.warning("Redis client not initialized. Cannot get key.")
            return None
        try:
            return await self._redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key '{key}' from Redis: {e}")
            return None

    async def delete(self, key: str):
        """Deletes a key from Redis."""
        if not self._redis_client:
            logger.warning("Redis client not initialized. Cannot delete key.")
            return
        try:
            await self._redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete key '{key}' from Redis: {e}")
