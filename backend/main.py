from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import random
from pathlib import Path
import numpy as np
from itertools import product
import tempfile

from logger import logger, log_info, log_warning, log_error, log_debug, get_log_level, set_log_level, LogLevel
from embeddings import (
    generate_clip_embedding, generate_fashion_embedding,
    classify_weather_labels, classify_formality_labels,
    load_category_centroids, classify_category
)
from config import get_settings
from storage import get_storage_client
import db

app = FastAPI(
    title="Wardrobe Recommendation API",
    description="API for wardrobe recommendation system with PostgreSQL and vector similarity",
    version="2.0.0"
)

# Initialize settings
settings = get_settings()

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup."""
    log_info("Starting up closetGPT API...")
    db.init_db_pool()
    log_info(f"Environment: {settings.env}")
    log_info(f"Storage Provider: {settings.storage_provider}")
    log_info("Database connection pool initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown."""
    log_info("Shutting down closetGPT API...")
    db.close_db_pool()
    log_info("Database connection pool closed")

# ========================
# Module-level caching
# ========================
_cached_centroids = None

# ========================
# Pydantic Models
# ========================

class ClothingItem(BaseModel):
    id: int
    category: str
    color: str
    formality: str
    name: Optional[str] = None
    image_path: Optional[str] = None

class RecommendRequest(BaseModel):
    selected_items: List[int] = Field(..., description="List of selected item IDs")
    weather: str = Field(..., description="Weather condition (e.g., cold, warm, hot)")
    occasion: str = Field(..., description="Occasion type (e.g., work, casual, formal)")

class SingleOutfit(BaseModel):
    items: List[ClothingItem]
    score: float

class OutfitRecommendation(BaseModel):
    recommended_outfits: List[SingleOutfit]
    reasoning: str

class ScoreRequest(BaseModel):
    item_ids: List[int] = Field(..., description="List of item IDs to score")

class ScoreResponse(BaseModel):
    score: float
    item_ids: List[int]

class VoteRequest(BaseModel):
    item_ids: List[int] = Field(..., description="List of item IDs in the outfit")
    vote: int = Field(..., description="Vote value: +1 for like, -1 for dislike")

class VoteResponse(BaseModel):
    success: bool
    message: str
    updated_items: List[int]

class UpdateMetadataRequest(BaseModel):
    item_id: int = Field(..., description="ID of the item to update")
    category: Optional[str] = Field(None, description="New category")
    weather_labels: Optional[List[str]] = Field(None, description="List of weather labels")
    formality_labels: Optional[List[str]] = Field(None, description="List of formality labels")

class UpdateMetadataResponse(BaseModel):
    success: bool
    message: str
    item_id: int

class UploadImageResponse(BaseModel):
    success: bool
    message: str
    item_id: int
    filename: str

class DeleteItemResponse(BaseModel):
    success: bool
    message: str
    item_id: int

class LogLevelRequest(BaseModel):
    level: str = Field(..., description="Log level: CRITICAL, ERROR, WARNING, INFO, DEBUG")

class LogLevelResponse(BaseModel):
    success: bool
    message: str
    current_level: str

# ========================
# Helper: Health Check
# ========================

@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "version": "2.0.0"}

# ========================
# API Endpoints
# ========================

@app.get("/")
def root():
    return {
        "message": "Wardrobe Recommendation API",
        "endpoints": [
            "GET /items - Get all wardrobe items",
            "GET /items/{item_id} - Get specific item",
            "POST /recommend - Get outfit recommendations",
            "POST /score - Score outfit compatibility"
        ]
    }

@app.get("/items")
def get_items():
    """
    Get all wardrobe items from PostgreSQL database.
    Returns items with image URLs from storage (MinIO/R2).
    """
    log_debug("Querying database for items...")

    try:
        items = db.get_all_items()
        log_debug(f"Retrieved {len(items)} items from database")
        return items
    except Exception as e:
        log_error(f"Error fetching items from database", exception=e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/items/{item_id}")
def get_item(item_id: int):
    """
    Get a specific wardrobe item by ID from PostgreSQL.
    """
    log_debug(f"Fetching item {item_id} from database...")

    try:
        item = db.get_item_by_id(item_id)

        if not item:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

        return item
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error fetching item {item_id}", exception=e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def load_metadata():
    """
    Load item information with labels from PostgreSQL database.
    Returns dictionary mapping category to list of items.
    """
    try:
        all_items = db.get_all_items()

        items_by_category = {}

        for item in all_items:
            category = item['category'].lower()

            if category not in items_by_category:
                items_by_category[category] = []

            items_by_category[category].append({
                'id': item['id'],
                'category': category,
                'image_path': item['image_url'],  # Full URL from storage
                'name': item['image_name'],
                'weather_label': item['weather_label'],
                'formality_label': item['formality_label'],
            })

        return items_by_category

    except Exception as e:
        log_error(f"Error loading metadata from database", exception=e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def get_items_for_category(items, max_count=20):
    """
    Get up to max_count items from a category, preferring items with metadata labels.
    """
    if len(items) == 0:
        return []

    # If we have <= max_count items, return all
    if len(items) <= max_count:
        return items

    # Otherwise, prioritize items with non-zero labels (assumed to have metadata)
    # and return max_count items
    prioritized = sorted(items, key=lambda x: (x['weather_label'] > 0, x['formality_label'] > 0), reverse=True)
    return prioritized[:max_count]


def encode_weather_labels(labels: List[str]) -> int:
    """
    Encode weather label strings to binary representation.
    Hot=0b0001, Cold=0b0010, Rainy=0b0100
    """
    weather_map = {
        'Hot': 0b0001,
        'Cold': 0b0010,
        'Rainy': 0b0100,
    }
    result = 0
    for label in labels:
        if label in weather_map:
            result |= weather_map[label]
    return result


def encode_formality_labels(labels: List[str]) -> int:
    """
    Encode formality label strings to binary representation.
    Casual=0b0001, Formal=0b0010, Sports=0b0100, Party=0b1000
    """
    formality_map = {
        'Casual': 0b0001,
        'Formal': 0b0010,
        'Sports': 0b0100,
        'Party': 0b1000,
    }
    result = 0
    for label in labels:
        if label in formality_map:
            result |= formality_map[label]
    return result


def preprocess_image(file_path: str, item_id: int = None) -> dict:
    """
    Preprocess an image to extract metadata using CLIP and FashionCLIP embeddings.
    Generates embeddings but does not save them (save happens after metadata.csv is updated).
    Uses centroid-based classification to infer category from FashionCLIP embedding.

    Args:
        file_path: Path to the image file
        item_id: ID of the item. Used to include embeddings in response.

    Returns:
        dict with category, weather_label, formality_label, clip_embedding, fashion_embedding
    """
    try:
        log_debug(f"Preprocessing image: {file_path}")

        # Generate CLIP embedding (used for weather/formality classification)
        clip_embedding = generate_clip_embedding(file_path)

        # Generate FashionCLIP embedding (used for category classification and outfit recommendations)
        fashion_embedding = None
        if item_id is not None:
            try:
                fashion_embedding = generate_fashion_embedding(file_path)
                log_debug(f"Generated FashionCLIP embedding for item {item_id}")
            except Exception as e:
                log_error(f"Failed to generate FashionCLIP embedding for {file_path}", exception=e)
                # Continue despite FashionCLIP failure - CLIP embedding is sufficient for labels

        # Classify weather and formality labels (using CLIP embedding)
        weather_label = classify_weather_labels(clip_embedding)
        formality_label = classify_formality_labels(clip_embedding)

        # Classify category using FashionCLIP embedding and pre-computed centroids
        category = "unknown"
        if fashion_embedding is not None:
            centroids = get_cached_centroids()
            if centroids:
                category = classify_category(fashion_embedding, centroids, threshold=0.25)
                log_debug(f"Classified category as '{category}' using FashionCLIP centroid matching")
            else:
                log_warning(f"Category centroids not available; defaulting to 'unknown'")

        result = {
            "metadata": {
                "category": category,
                "weather_label": int(weather_label),
                "formality_label": int(formality_label),
            },
            "clip_embedding": clip_embedding,
            "fashion_embedding": fashion_embedding,
        }

        log_debug(f"Preprocessing complete for {file_path}")
        return result

    except Exception as e:
        log_error(f"Error preprocessing image", exception=e)
        # Return default metadata on error
        return {
            "metadata": {
                "category": "unknown",
                "weather_label": 0,
                "formality_label": 0,
            },
            "clip_embedding": None,
            "fashion_embedding": None,
        }


def get_cached_centroids() -> dict:
    """
    Get cached category centroids, loading from disk if not already cached.
    Centroids are loaded once and reused for subsequent classification requests.

    Returns:
        Dictionary mapping category names to centroid embeddings.
        Returns empty dict if centroids file doesn't exist.
    """
    global _cached_centroids
    if _cached_centroids is None:
        embeddings_dir = Path("../wardrobe-app/public")
        _cached_centroids = load_category_centroids(embeddings_dir=str(embeddings_dir))
        if _cached_centroids:
            log_debug(f"Loaded {len(_cached_centroids)} category centroids into cache")
    return _cached_centroids


def load_embeddings():
    """
    Load FashionCLIP embeddings from PostgreSQL database.
    Returns numpy array of embeddings indexed by (item_id - 1).
    """
    try:
        item_ids, embeddings = db.get_all_fashion_embeddings()

        if len(item_ids) == 0:
            log_warning("No embeddings found in database. Outfit scoring will use default scores.")
            return None

        # Create array indexed by item_id (1-indexed, so array is 0-indexed)
        max_id = max(item_ids)
        embeddings_array = np.zeros((max_id, embeddings.shape[1]))

        for i, item_id in enumerate(item_ids):
            embeddings_array[item_id - 1] = embeddings[i]

        log_debug(f"Loaded {len(item_ids)} embeddings from database")
        return embeddings_array

    except Exception as e:
        log_error(f"Error loading embeddings from database", exception=e)
        return None


def calculate_outfit_score(outfit_items, embeddings):
    """
    Calculate outfit compatibility score using FashionCLIP embeddings.
    Uses cosine similarity between item embeddings to measure compatibility.

    Args:
        outfit_items: List of item dictionaries with 'id' field
        embeddings: Numpy array of shape (num_items, embedding_dim)

    Returns:
        float: Outfit compatibility score between 0 and 1
    """
    if embeddings is None or len(outfit_items) < 2:
        return 0.5

    # Get embeddings for the outfit items
    item_ids = [item['id'] for item in outfit_items]
    item_embeddings = []

    for item_id in item_ids:
        # item_id is 1-indexed, but array is 0-indexed
        idx = item_id - 1
        if 0 <= idx < len(embeddings):
            item_embeddings.append(embeddings[idx])

    if len(item_embeddings) < 2:
        return 0.5

    # Calculate pairwise cosine similarities
    similarities = []
    for i in range(len(item_embeddings)):
        for j in range(i + 1, len(item_embeddings)):
            emb1 = item_embeddings[i]
            emb2 = item_embeddings[j]
            # Cosine similarity (embeddings are L2 normalized)
            sim = np.dot(emb1, emb2)
            similarities.append(sim)

    # Average similarity across all pairs, scaled to 0-1
    avg_similarity = np.mean(similarities) if similarities else 0.5
    # Map from [-1, 1] to [0, 1]
    score = (avg_similarity + 1) / 2

    return float(score)


def select_diverse_outfits(outfit_combinations, outfit_scores, top_k=5):
    """
    Select top-K diverse outfits by randomly sampling from top 20-30 outfits.

    Args:
        outfit_combinations: List of outfit combinations (each is a list of items)
        outfit_scores: List of scores corresponding to each outfit
        top_k: Number of diverse outfits to select

    Returns:
        List of top-K diverse outfits with their scores
    """
    # Create list of (outfit, score) tuples and sort by score (descending)
    outfit_score_pairs = list(zip(outfit_combinations, outfit_scores))
    outfit_score_pairs.sort(key=lambda x: x[1], reverse=True)

    # Select from top 20-30 outfits (or fewer if not enough exist)
    candidate_pool_size = min(30, max(20, len(outfit_score_pairs) // 10))
    candidate_pool = outfit_score_pairs[:candidate_pool_size]

    # Shuffle to randomize selection
    random.shuffle(candidate_pool)

    diverse_outfits = []
    item_usage_count = {}

    for outfit, score in candidate_pool:
        if len(diverse_outfits) >= top_k:
            break

        outfit_item_ids = [item['id'] for item in outfit]

        # Ensure no item appears in more than 2 outfits
        can_use_outfit = True
        for item_id in outfit_item_ids:
            if item_usage_count.get(item_id, 0) >= 2:
                can_use_outfit = False
                break

        if can_use_outfit:
            diverse_outfits.append((outfit, score))
            for item_id in outfit_item_ids:
                item_usage_count[item_id] = item_usage_count.get(item_id, 0) + 1

    # If we still don't have enough, relax to allow items in up to 3 outfits
    if len(diverse_outfits) < top_k:
        for outfit, score in candidate_pool:
            if len(diverse_outfits) >= top_k:
                break

            outfit_item_ids = [item['id'] for item in outfit]
            existing_ids = [tuple(sorted([item['id'] for item in o])) for o, _ in diverse_outfits]

            # Skip if already selected
            if tuple(sorted(outfit_item_ids)) in existing_ids:
                continue

            # Check if any item would exceed 3 outfits
            can_use_outfit = True
            for item_id in outfit_item_ids:
                if item_usage_count.get(item_id, 0) >= 3:
                    can_use_outfit = False
                    break

            if can_use_outfit:
                diverse_outfits.append((outfit, score))
                for item_id in outfit_item_ids:
                    item_usage_count[item_id] = item_usage_count.get(item_id, 0) + 1

    return diverse_outfits


def generate_outfit_combinations(category_items_dict, required_categories):
    """
    Generate outfit combinations using hybrid approach:
    1. Random sampling: randomly select items from each category
    2. Greedy approach: keep the best combinations

    Args:
        category_items_dict: Dict mapping category -> list of items
        required_categories: List of required categories

    Returns:
        List of outfit combinations (each is a list of items, one per category)
    """
    # Get items for each category (up to 20)
    category_selections = {}
    for category in required_categories:
        category_items = get_items_for_category(category_items_dict[category])
        category_selections[category] = category_items

    # Calculate total combinations
    total_combinations = 1
    for category in required_categories:
        total_combinations *= len(category_selections[category])

    # If total combinations <= 5000, generate all; otherwise use sampling
    if total_combinations <= 5000:
        # Generate all combinations
        category_lists = [category_selections[cat] for cat in required_categories]
        combinations = list(product(*category_lists))
        # Convert tuples to lists
        combinations = [list(combo) for combo in combinations]
    else:
        # Hybrid random sampling + greedy approach
        # Sample random combinations, keep top candidates
        num_samples = min(5000, total_combinations)
        combinations = []
        seen = set()

        for _ in range(num_samples):
            combination = []
            combo_ids = []
            for category in required_categories:
                item = random.choice(category_selections[category])
                combination.append(item)
                combo_ids.append(item['id'])

            # Use item IDs as unique key to avoid duplicates
            combo_key = tuple(combo_ids)
            if combo_key not in seen:
                seen.add(combo_key)
                combinations.append(combination)

    return combinations


@app.post("/recommend", response_model=OutfitRecommendation)
def recommend_outfit(request: RecommendRequest):
    """
    Generate outfit recommendations based on weather, occasion, and metadata.

    All outfits include: shoes, bottoms, and tops.
    Cold/rainy weather also includes outerwear.
    Generates all possible outfit combinations and returns the best-scored one.
    """
    log_debug(f"Calling outfit generation model with context: {request.weather}, {request.occasion}")
    log_debug(f"Selected items: {request.selected_items}")

    # Load items from metadata and embeddings
    items_by_category = load_metadata()
    embeddings = load_embeddings()

    # Required categories for an outfit
    required_categories = []

    # Add outerwear for cold or rainy weather
    if request.weather.lower() in ['cold', 'rainy']:
        required_categories.append('outerwear')

    required_categories += ['tops', 'bottoms', 'shoes']

    # Check that we have required categories
    for category in required_categories:
        if category not in items_by_category or len(items_by_category[category]) == 0:
            raise HTTPException(status_code=500, detail=f"No items found in {category} category")

    # Generate outfit combinations
    outfit_combinations = generate_outfit_combinations(items_by_category, required_categories)

    if not outfit_combinations:
        raise HTTPException(status_code=500, detail="Failed to generate outfit combinations")

    # Score each outfit
    all_scores = []
    for outfit_combo in outfit_combinations:
        score = calculate_outfit_score(outfit_combo, embeddings)
        all_scores.append(score)

    # Log scores
    avg_score = np.mean(all_scores)
    max_score = np.max(all_scores)
    min_score = np.min(all_scores)
    log_info(f"Outfit Scores - Best: {max_score:.4f}, Avg: {avg_score:.4f}, Min: {min_score:.4f}, Max: {max_score:.4f}")

    # Select top-5 diverse outfits
    diverse_outfits = select_diverse_outfits(outfit_combinations, all_scores, top_k=5)

    # Convert to response format
    recommended_outfits = []
    for outfit_combo, score in diverse_outfits:
        outfit_items = []
        for item_data in outfit_combo:
            item = ClothingItem(
                id=item_data['id'],
                category=item_data['category'],
                color="unknown",
                formality="casual",
                name=item_data['name'],
                image_path=item_data['image_path']
            )
            outfit_items.append(item)

        recommended_outfits.append(SingleOutfit(items=outfit_items, score=round(score, 4)))

    # Log top-5 scores
    top_scores = [score for _, score in diverse_outfits]
    log_info(f"Top-5 Diverse Outfit Scores: {[round(s, 4) for s in top_scores]}")

    reasoning = f"Based on {request.weather} weather and {request.occasion} occasion, " \
                f"selected top-5 diverse outfits with scores: {[round(s, 4) for s in top_scores]}"

    return OutfitRecommendation(
        recommended_outfits=recommended_outfits,
        reasoning=reasoning
    )

@app.post("/score", response_model=ScoreResponse)
def score_outfit(request: ScoreRequest):
    """
    Score the compatibility of a set of items
    """
    # TODO: Replace with actual ML model call
    # Example: score = compatibility_model.score(item_ids)

    log_debug(f"Calling compatibility scoring model for items: {request.item_ids}")

    # Dummy logic: generate random score between 0.0 and 1.0
    # In reality, this would be based on color theory, style rules, etc.
    score = round(random.uniform(0.5, 1.0), 2)

    return ScoreResponse(
        score=score,
        item_ids=request.item_ids
    )

@app.post("/vote", response_model=VoteResponse)
def vote_outfit(request: VoteRequest):
    """
    Record user feedback on an outfit by voting on items.
    +1 for like (positive feedback), -1 for dislike (negative feedback)
    Updates the vote_score in PostgreSQL for each item in the outfit.
    """
    try:
        updated_count = db.update_item_votes(request.item_ids, request.vote)

        if updated_count == 0:
            raise HTTPException(status_code=404, detail="No items found to update")

        vote_type = "liked" if request.vote > 0 else "disliked"
        log_info(f"Outfit {vote_type}: updated {updated_count} items")

        return VoteResponse(
            success=True,
            message=f"Outfit {vote_type} successfully. Updated {updated_count} items.",
            updated_items=request.item_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error updating votes", exception=e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/update-metadata", response_model=UpdateMetadataResponse)
def update_metadata(request: UpdateMetadataRequest):
    """
    Update item metadata (category, weather labels, formality labels) in PostgreSQL.
    Only provided fields are updated.
    """
    try:
        # Encode label lists to binary if provided
        weather_binary = None
        if request.weather_labels is not None:
            weather_binary = encode_weather_labels(request.weather_labels)

        formality_binary = None
        if request.formality_labels is not None:
            formality_binary = encode_formality_labels(request.formality_labels)

        # Update in database
        success = db.update_item_metadata(
            item_id=request.item_id,
            category=request.category,
            weather_label=weather_binary,
            formality_label=formality_binary
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Item {request.item_id} not found")

        log_info(f"Item {request.item_id} metadata updated successfully")

        return UpdateMetadataResponse(
            success=True,
            message=f"Item {request.item_id} metadata updated successfully",
            item_id=request.item_id
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error updating metadata", exception=e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/upload-image", response_model=UploadImageResponse)
def upload_image(image: UploadFile = File(...)):
    """
    Upload a new wardrobe image:
    1. Upload image to storage (MinIO/R2)
    2. Generate embeddings with CLIP/FashionCLIP
    3. Insert metadata and embeddings into PostgreSQL
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        filename = image.filename
        if not filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Read image data
        image_data = image.file.read()

        # Save to temporary file for processing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp_file:
            tmp_file.write(image_data)
            tmp_file_path = tmp_file.name

        try:
            # Preprocess image to extract metadata and embeddings
            # Pass None for item_id since we don't have it yet
            preprocess_result = preprocess_image(tmp_file_path, item_id=1)
            metadata = preprocess_result['metadata']
            clip_embedding = preprocess_result['clip_embedding']
            fashion_embedding = preprocess_result['fashion_embedding']

            if clip_embedding is None or fashion_embedding is None:
                raise HTTPException(status_code=500, detail="Failed to generate embeddings")

            # Upload image to storage
            storage_client = get_storage_client()
            object_key = f"uploads/{filename}"
            image_url_internal, image_url_public = storage_client.upload_file(
                image_data,
                object_key,
                content_type=image.content_type
            )

            log_debug(f"Uploaded image to storage: {image_url_public}")

            # Insert into database
            item_id = db.insert_clothing_item(
                image_name=filename,
                image_url_internal=image_url_internal,
                image_url_public=image_url_public,
                category=metadata['category'],
                weather_label=metadata['weather_label'],
                formality_label=metadata['formality_label']
            )

            # Insert embeddings
            db.insert_item_embeddings(
                item_id=item_id,
                clip_embedding=clip_embedding,
                fashion_embedding=fashion_embedding
            )

            log_info(f"Successfully uploaded item {item_id}: {filename}")

            return UploadImageResponse(
                success=True,
                message=f"Image uploaded successfully",
                item_id=item_id,
                filename=filename
            )

        finally:
            # Clean up temporary file
            try:
                Path(tmp_file_path).unlink()
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error uploading image", exception=e)
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@app.get("/config/log-level", response_model=LogLevelResponse)
def get_log_level_endpoint():
    """
    Get the current log level setting.
    """
    current_level = get_log_level()
    return LogLevelResponse(
        success=True,
        message=f"Current log level is {current_level.value}",
        current_level=current_level.value
    )


@app.post("/config/log-level", response_model=LogLevelResponse)
def set_log_level_endpoint(request: LogLevelRequest):
    """
    Set the log level at runtime. Changes take effect immediately.

    Valid levels: CRITICAL, ERROR, WARNING, INFO, DEBUG
    """
    try:
        level = LogLevel(request.level.upper())
        set_log_level(level)
        return LogLevelResponse(
            success=True,
            message=f"Log level changed to {level.value}",
            current_level=level.value
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log level. Must be one of: CRITICAL, ERROR, WARNING, INFO, DEBUG"
        )


@app.delete("/delete-item/{item_id}", response_model=DeleteItemResponse)
def delete_item(item_id: int):
    """
    Delete a wardrobe item completely:
    1. Delete from PostgreSQL (embeddings deleted via CASCADE)
    2. Delete image from storage (MinIO/R2)
    """
    try:
        # Delete from database (returns image URL)
        success, image_url = db.delete_clothing_item(item_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

        # Delete from storage if we have an image URL
        if image_url:
            try:
                storage_client = get_storage_client()
                # Extract object key from URL
                # URL format: http://minio:9000/bucket/path or https://r2.../path
                object_key = image_url.split('/')[-1]  # Simplified extraction
                if '/' in image_url.split(storage_client.bucket)[-1]:
                    object_key = image_url.split(storage_client.bucket + '/')[-1]

                storage_client.delete_file(object_key)
                log_debug(f"Deleted image from storage: {object_key}")
            except Exception as e:
                log_warning(f"Failed to delete image from storage: {e}")
                # Continue even if storage deletion fails

        log_info(f"Item {item_id} deleted successfully")

        return DeleteItemResponse(
            success=True,
            message=f"Item {item_id} deleted successfully",
            item_id=item_id
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error deleting item", exception=e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
