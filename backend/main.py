from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import random
import csv
from pathlib import Path
import numpy as np
from itertools import product

app = FastAPI(
    title="Wardrobe Recommendation API",
    description="Dummy API for wardrobe recommendation system",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ========================
# Dummy Database
# ========================

# TODO: Replace with real database queries (PostgreSQL, MongoDB, etc.)
DUMMY_ITEMS = [
    {
        "id": 1,
        "category": "tops",
        "color": "white",
        "formality": "business-casual",
        "name": "White Oxford Shirt",
        "image_path": "/wardrobe/shirt_1.jpg"
    },
    {
        "id": 2,
        "category": "bottoms",
        "color": "navy",
        "formality": "business-casual",
        "name": "Navy Chinos",
        "image_path": "/wardrobe/pants_1.jpg"
    },
    {
        "id": 3,
        "category": "outerwear",
        "color": "black",
        "formality": "formal",
        "name": "Black Blazer",
        "image_path": "/wardrobe/blazer_1.jpg"
    },
    {
        "id": 4,
        "category": "shoes",
        "color": "brown",
        "formality": "casual",
        "name": "Brown Loafers",
        "image_path": "/wardrobe/shoes_1.jpg"
    },
    {
        "id": 5,
        "category": "tops",
        "color": "gray",
        "formality": "casual",
        "name": "Gray Hoodie",
        "image_path": "/wardrobe/hoodie_1.jpg"
    }
]

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

@app.get("/items", response_model=List[ClothingItem])
def get_items():
    """
    Get all wardrobe items from database
    """
    # TODO: Replace with actual database query
    # Example: items = db.query(ClothingItem).all()

    print("Querying database for items...")

    return DUMMY_ITEMS

@app.get("/items/{item_id}", response_model=ClothingItem)
def get_item(item_id: int):
    """
    Get a specific wardrobe item by ID
    """
    # TODO: Replace with actual database query
    # Example: item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()

    print(f"Fetching item {item_id} from database...")

    item = next((item for item in DUMMY_ITEMS if item["id"] == item_id), None)

    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    return item

def load_metadata():
    """
    Load and parse metadata.csv to get item information with labels
    """
    metadata_path = Path("../wardrobe-app/public/metadata.csv")

    if not metadata_path.exists():
        raise HTTPException(status_code=500, detail="Metadata file not found")

    items_by_category = {}

    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_id = int(row['id'])
            category = row['item_category'].lower()
            weather_label = int(row['weather_label'])
            formality_label = int(row['formality_label'])

            if category not in items_by_category:
                items_by_category[category] = []

            items_by_category[category].append({
                'id': item_id,
                'category': category,
                'image_path': f"/wardrobe/{row['image_path']}",
                'name': row['image_name'],
                'weather_label': weather_label,
                'formality_label': formality_label,
            })

    return items_by_category


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


def load_embeddings():
    """
    Load FashionCLIP embeddings from fashion_embeddings.npy file.
    Returns a dictionary mapping item_id to embedding vector.
    """
    embeddings_path = Path("../wardrobe-app/public/fashion_embeddings.npy")

    if not embeddings_path.exists():
        print("Warning: fashion_embeddings.npy not found. Outfit scoring will not use embeddings.")
        return None

    try:
        embeddings = np.load(embeddings_path)
        return embeddings
    except Exception as e:
        print(f"Error loading embeddings: {e}")
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
    print(f"Calling outfit generation model with context: {request.weather}, {request.occasion}")
    print(f"Selected items: {request.selected_items}")

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

    # Print scores to terminal
    avg_score = np.mean(all_scores)
    max_score = np.max(all_scores)
    min_score = np.min(all_scores)
    print(f"Outfit Scores - Best: {max_score:.4f}, Avg: {avg_score:.4f}, Min: {min_score:.4f}, Max: {max_score:.4f}")

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

    # Print top-5 scores
    top_scores = [score for _, score in diverse_outfits]
    print(f"Top-5 Diverse Outfit Scores: {[round(s, 4) for s in top_scores]}")

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

    print(f"Calling compatibility scoring model for items: {request.item_ids}")

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
    Updates the vote column in metadata.csv for each item in the outfit.
    """
    metadata_path = Path("../wardrobe-app/public/metadata.csv")

    if not metadata_path.exists():
        raise HTTPException(status_code=500, detail="Metadata file not found")

    try:
        # Read the CSV file
        rows = []

        with open(metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if 'vote' not in headers:
                raise HTTPException(status_code=400, detail="Vote column not found in metadata.csv")

            for row in reader:
                rows.append(row)

        # Update votes for items in the outfit
        updated_count = 0
        for row in rows:
            item_id = int(row['id'])
            if item_id in request.item_ids:
                current_vote = int(row.get('vote', 0))
                row['vote'] = str(current_vote + request.vote)
                updated_count += 1

        # Write back to CSV
        with open(metadata_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        vote_type = "liked" if request.vote > 0 else "disliked"
        return VoteResponse(
            success=True,
            message=f"Outfit {vote_type} successfully. Updated {updated_count} items.",
            updated_items=request.item_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating votes: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating votes: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
