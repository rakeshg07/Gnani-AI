"""MongoDB database connection and collection management for VoiceIQ India."""
from typing import Generator, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
import mongomock
from app.core.config import settings
from app.core.logging import logger

_mongo_client: Any = None
_is_mock: bool = False


def get_mongo_client() -> Any:
    """Returns singleton MongoDB client, with automatic in-process fallback if daemon offline."""
    global _mongo_client, _is_mock
    if _mongo_client is not None:
        return _mongo_client

    try:
        # Attempt connecting to configured MongoDB URI (default mongodb://localhost:27017)
        client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=5000,
        )
        # Test connection ping
        client.admin.command("ping")
        _mongo_client = client
        _is_mock = False
        logger.info(f"Successfully connected to MongoDB server at {settings.MONGODB_URI}")
    except Exception as conn_err:
        logger.warning(
            f"Live MongoDB not available ({conn_err}). Initializing in-process MongoDB engine (mongomock)."
        )
        _mongo_client = mongomock.MongoClient()
        _is_mock = True

    return _mongo_client


def get_mongo_db() -> Any:
    """Returns the VoiceIQ MongoDB database instance."""
    client = get_mongo_client()
    return client[settings.MONGODB_DB_NAME]


def get_db() -> Generator[Any, None, None]:
    """FastAPI dependency that yields the VoiceIQ MongoDB database instance."""
    db = get_mongo_db()
    try:
        yield db
    finally:
        pass


def is_mock_db() -> bool:
    """Returns True if running in in-process mongomock mode."""
    global _is_mock
    return _is_mock


def init_db() -> None:
    """Initializes MongoDB collections, schemas, and necessary indexes."""
    db = get_mongo_db()
    logger.info(f"Initializing MongoDB collections and indexes for database: {settings.MONGODB_DB_NAME}")

    try:
        # Create indexes for high query performance
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("id", ASCENDING)], unique=True)

        db.categories.create_index([("id", ASCENDING)], unique=True)
        db.categories.create_index([("slug", ASCENDING)])

        db.products.create_index([("id", ASCENDING)], unique=True)
        db.products.create_index([("category_id", ASCENDING)])
        db.products.create_index([("slug", ASCENDING)])
        db.products.create_index([("price", ASCENDING)])

        db.carts.create_index([("customer_id", ASCENDING)], unique=True)
        db.orders.create_index([("id", ASCENDING)], unique=True)
        db.orders.create_index([("customer_id", ASCENDING)])
        db.orders.create_index([("created_at", DESCENDING)])

        db.return_requests.create_index([("id", ASCENDING)], unique=True)
        db.return_requests.create_index([("order_id", ASCENDING)])

        db.pending_actions.create_index([("confirmation_token", ASCENDING)], unique=True)
        db.pending_actions.create_index([("id", ASCENDING)], unique=True)

        db.conversations.create_index([("id", ASCENDING)], unique=True)
        db.conversations.create_index([("created_at", DESCENDING)])
        db.conversations.create_index([("language_code", ASCENDING)])

        logger.info("MongoDB indexes verified successfully.")
    except Exception as idx_err:
        logger.warning(f"MongoDB index setup notice: {idx_err}")
