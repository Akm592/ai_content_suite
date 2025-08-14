# backend/redis_client.py
import redis
import os
import logging

logger = logging.getLogger(__name__)

# Connect to Redis using environment variables for flexibility
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    # Create a single, reusable connection pool for efficiency
    pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client = redis.Redis(connection_pool=pool)
    # Check the connection
    redis_client.ping()
    logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.exceptions.ConnectionError as e:
    logger.critical(f"FATAL: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Please ensure Redis is running. Error: {e}")
    # Exit if Redis is not available, as it's a critical dependency
    exit(1)

def get_redis_client():
    """
    Returns the shared Redis client instance.
    """
    return redis_client