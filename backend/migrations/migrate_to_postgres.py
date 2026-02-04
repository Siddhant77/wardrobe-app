"""
Migration script to transfer data from CSV/NPY files to PostgreSQL.
This script:
1. Reads metadata.csv
2. Loads embedding files (.npy)
3. Uploads images to storage (MinIO/R2)
4. Inserts data into PostgreSQL with pgvector
"""

import csv
import sys
from pathlib import Path
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

# Add parent directory to path to import config and storage
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from storage import get_storage_client


# Paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
METADATA_CSV = PROJECT_ROOT / "wardrobe-app" / "public" / "metadata.csv"
CLIP_EMBEDDINGS = PROJECT_ROOT / "wardrobe-app" / "public" / "vit_embeddings.npy"
FASHION_EMBEDDINGS = PROJECT_ROOT / "wardrobe-app" / "public" / "fashion_embeddings.npy"
IMAGES_DIR = PROJECT_ROOT / "wardrobe-app" / "public" / "wardrobe"

# Default user ID for development (before authentication)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"


def load_metadata():
    """Load metadata from CSV file."""
    print(f"Loading metadata from {METADATA_CSV}...")
    items = []
    with open(METADATA_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    print(f"Loaded {len(items)} items from CSV")
    return items


def load_embeddings():
    """Load embeddings from .npy files."""
    print(f"Loading CLIP embeddings from {CLIP_EMBEDDINGS}...")
    clip_emb = np.load(CLIP_EMBEDDINGS)
    print(f"Loaded CLIP embeddings: {clip_emb.shape}")

    print(f"Loading Fashion embeddings from {FASHION_EMBEDDINGS}...")
    fashion_emb = np.load(FASHION_EMBEDDINGS)
    print(f"Loaded Fashion embeddings: {fashion_emb.shape}")

    return clip_emb, fashion_emb


def upload_image_to_storage(image_path: Path, storage_client) -> str:
    """
    Upload image to storage and return public URL.

    Args:
        image_path: Local path to image file
        storage_client: Storage client instance

    Returns:
        Public URL of uploaded image
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Read image file
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Generate object key (preserve directory structure)
    object_key = f"wardrobe/{image_path.parent.name}/{image_path.name}"

    # Determine content type
    content_type = "image/jpeg"
    if image_path.suffix.lower() in [".png"]:
        content_type = "image/png"
    elif image_path.suffix.lower() in [".heic"]:
        content_type = "image/heic"

    # Upload to storage
    internal_url, public_url = storage_client.upload_file(image_data, object_key, content_type)
    return internal_url, public_url


def connect_to_database():
    """Connect to PostgreSQL database."""
    settings = get_settings()
    print(f"Connecting to database...")

    conn = psycopg2.connect(settings.database_url)
    print("Connected to PostgreSQL")
    return conn


def migrate_data():
    """Main migration function."""
    print("=" * 60)
    print("closetGPT Data Migration")
    print("=" * 60)

    # Load data
    metadata_items = load_metadata()
    clip_embeddings, fashion_embeddings = load_embeddings()

    # Validate data consistency
    if len(metadata_items) != len(clip_embeddings):
        print(f"ERROR: Mismatch between metadata ({len(metadata_items)}) and CLIP embeddings ({len(clip_embeddings)})")
        sys.exit(1)
    if len(metadata_items) != len(fashion_embeddings):
        print(f"ERROR: Mismatch between metadata ({len(metadata_items)}) and Fashion embeddings ({len(fashion_embeddings)})")
        sys.exit(1)

    # Initialize storage and database
    storage_client = get_storage_client()
    conn = connect_to_database()
    cursor = conn.cursor()

    print("\nStarting migration...")
    print("-" * 60)

    successful_migrations = 0
    failed_migrations = 0

    for idx, item in enumerate(tqdm(metadata_items, desc="Migrating items")):
        try:
            # Parse metadata
            item_id = int(item["id"])
            image_name = item["image_name"]
            image_path_rel = item["image_path"]
            category = item["item_category"]
            weather = int(item["weather_label"])
            formality = int(item["formality_label"])
            vote = int(item["vote"])

            # Upload image to storage
            local_image_path = IMAGES_DIR / image_path_rel
            image_url_internal, image_url_public = upload_image_to_storage(local_image_path, storage_client)

            # Insert clothing item
            cursor.execute(
                """
                INSERT INTO clothing_items (item_id, user_id, image_name, image_url_internal,
                                           image_url_public, item_category,
                                           weather_label, formality_label, vote_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_id) DO UPDATE SET
                    image_url_internal = EXCLUDED.image_url_internal,
                    image_url_public = EXCLUDED.image_url_public,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (item_id, DEFAULT_USER_ID, image_name, image_url_internal, image_url_public, category, weather, formality, vote),
            )

            # Get embeddings for this item
            clip_emb = clip_embeddings[idx].tolist()
            fashion_emb = fashion_embeddings[idx].tolist()

            # Insert embeddings
            cursor.execute(
                """
                INSERT INTO item_embeddings (item_id, clip_embedding, fashion_embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (item_id) DO UPDATE SET
                    clip_embedding = EXCLUDED.clip_embedding,
                    fashion_embedding = EXCLUDED.fashion_embedding
                """,
                (item_id, clip_emb, fashion_emb),
            )

            successful_migrations += 1

        except Exception as e:
            print(f"\nERROR migrating item {item.get('id', 'unknown')}: {e}")
            failed_migrations += 1
            conn.rollback()
            continue

    # Commit all changes
    conn.commit()
    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"✅ Successful: {successful_migrations}")
    print(f"❌ Failed: {failed_migrations}")
    print(f"📊 Total: {len(metadata_items)}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        migrate_data()
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
