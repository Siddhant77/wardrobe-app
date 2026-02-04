"""
Database operations for closetGPT.
Handles PostgreSQL queries with connection pooling.
"""

from typing import List, Dict, Optional, Tuple
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import numpy as np

from config import get_settings
from logger import log_debug, log_error, log_warning


# Global connection pool
_pool: Optional[SimpleConnectionPool] = None

# Default user ID (before authentication in Phase 6)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"


def init_db_pool():
    """Initialize database connection pool."""
    global _pool
    if _pool is None:
        settings = get_settings()
        log_debug("Initializing database connection pool...")
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url
        )
        log_debug("Database connection pool initialized")


def close_db_pool():
    """Close database connection pool."""
    global _pool
    if _pool is not None:
        log_debug("Closing database connection pool...")
        _pool.closeall()
        _pool = None
        log_debug("Database connection pool closed")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    if _pool is None:
        init_db_pool()

    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        _pool.putconn(conn)


def get_all_items(user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """
    Get all clothing items for a user.

    Returns:
        List of item dictionaries with metadata
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT item_id as id, image_name, image_url_public as image_url, item_category as category,
                       weather_label, formality_label, vote_score, created_at
                FROM clothing_items
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            items = cursor.fetchall()
            return [dict(item) for item in items]


def get_item_by_id(item_id: int, user_id: str = DEFAULT_USER_ID) -> Optional[Dict]:
    """
    Get a specific clothing item by ID.

    Returns:
        Item dictionary or None if not found
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT item_id as id, image_name, image_url_public as image_url, item_category as category,
                       weather_label, formality_label, vote_score, created_at
                FROM clothing_items
                WHERE item_id = %s AND user_id = %s
                """,
                (item_id, user_id)
            )
            item = cursor.fetchone()
            return dict(item) if item else None


def insert_clothing_item(
    image_name: str,
    image_url_internal: str,
    image_url_public: str,
    category: str,
    weather_label: int,
    formality_label: int,
    user_id: str = DEFAULT_USER_ID
) -> int:
    """
    Insert a new clothing item.

    Returns:
        item_id of the newly created item
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO clothing_items (user_id, image_name, image_url_internal,
                                           image_url_public, item_category,
                                           weather_label, formality_label, vote_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                RETURNING item_id
                """,
                (user_id, image_name, image_url_internal, image_url_public, category, weather_label, formality_label)
            )
            item_id = cursor.fetchone()[0]
            return item_id


def insert_item_embeddings(
    item_id: int,
    clip_embedding: np.ndarray,
    fashion_embedding: np.ndarray
) -> None:
    """Insert embeddings for a clothing item."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO item_embeddings (item_id, clip_embedding, fashion_embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (item_id) DO UPDATE SET
                    clip_embedding = EXCLUDED.clip_embedding,
                    fashion_embedding = EXCLUDED.fashion_embedding
                """,
                (item_id, clip_embedding.tolist(), fashion_embedding.tolist())
            )


def update_item_metadata(
    item_id: int,
    category: Optional[str] = None,
    weather_label: Optional[int] = None,
    formality_label: Optional[int] = None,
    user_id: str = DEFAULT_USER_ID
) -> bool:
    """
    Update clothing item metadata.

    Returns:
        True if item was found and updated, False otherwise
    """
    # Build dynamic UPDATE query based on provided fields
    update_fields = []
    params = []

    if category is not None:
        update_fields.append("item_category = %s")
        params.append(category)

    if weather_label is not None:
        update_fields.append("weather_label = %s")
        params.append(weather_label)

    if formality_label is not None:
        update_fields.append("formality_label = %s")
        params.append(formality_label)

    if not update_fields:
        return False  # Nothing to update

    # Add updated_at
    update_fields.append("updated_at = CURRENT_TIMESTAMP")

    # Add WHERE clause params
    params.extend([item_id, user_id])

    query = f"""
        UPDATE clothing_items
        SET {', '.join(update_fields)}
        WHERE item_id = %s AND user_id = %s
    """

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount > 0


def update_item_votes(item_ids: List[int], vote: int, user_id: str = DEFAULT_USER_ID) -> int:
    """
    Update vote scores for multiple items.

    Returns:
        Number of items updated
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE clothing_items
                SET vote_score = vote_score + %s, updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ANY(%s) AND user_id = %s
                """,
                (vote, item_ids, user_id)
            )
            return cursor.rowcount


def delete_clothing_item(item_id: int, user_id: str = DEFAULT_USER_ID) -> Tuple[bool, Optional[str]]:
    """
    Delete a clothing item (also deletes embeddings via CASCADE).

    Returns:
        (success, image_url_internal) tuple for storage deletion
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Get internal image URL before deleting (for storage deletion)
            cursor.execute(
                "SELECT image_url_internal FROM clothing_items WHERE item_id = %s AND user_id = %s",
                (item_id, user_id)
            )
            result = cursor.fetchone()

            if not result:
                return False, None

            image_url_internal = result[0]

            # Delete item (embeddings deleted via CASCADE)
            cursor.execute(
                "DELETE FROM clothing_items WHERE item_id = %s AND user_id = %s",
                (item_id, user_id)
            )

            return cursor.rowcount > 0, image_url_internal


def get_embeddings_by_ids(item_ids: List[int], user_id: str = DEFAULT_USER_ID) -> Dict[int, Dict]:
    """
    Get embeddings for multiple items.

    Returns:
        Dictionary mapping item_id to {clip_embedding, fashion_embedding}
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.item_id, e.clip_embedding, e.fashion_embedding
                FROM item_embeddings e
                JOIN clothing_items c ON e.item_id = c.item_id
                WHERE e.item_id = ANY(%s) AND c.user_id = %s
                """,
                (item_ids, user_id)
            )
            results = cursor.fetchall()

            embeddings = {}
            for row in results:
                item_id, clip_emb, fashion_emb = row
                embeddings[item_id] = {
                    "clip_embedding": np.array(clip_emb),
                    "fashion_embedding": np.array(fashion_emb)
                }

            return embeddings


def get_all_fashion_embeddings(user_id: str = DEFAULT_USER_ID) -> Tuple[List[int], np.ndarray]:
    """
    Get all fashion embeddings for a user.

    Returns:
        (item_ids, embeddings_array) tuple
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.item_id, e.fashion_embedding
                FROM item_embeddings e
                JOIN clothing_items c ON e.item_id = c.item_id
                WHERE c.user_id = %s
                ORDER BY e.item_id
                """,
                (user_id,)
            )
            results = cursor.fetchall()

            if not results:
                return [], np.array([])

            item_ids = [row[0] for row in results]
            embeddings = np.array([row[1] for row in results])

            return item_ids, embeddings


def get_items_by_category(category: str, user_id: str = DEFAULT_USER_ID) -> List[Dict]:
    """Get all items in a specific category."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT item_id as id, image_name, image_url_public as image_url, item_category as category,
                       weather_label, formality_label, vote_score
                FROM clothing_items
                WHERE item_category = %s AND user_id = %s
                ORDER BY created_at DESC
                """,
                (category, user_id)
            )
            items = cursor.fetchall()
            return [dict(item) for item in items]
