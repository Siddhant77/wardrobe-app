from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import random

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

class OutfitRecommendation(BaseModel):
    recommended_items: List[ClothingItem]
    compatibility_score: float
    reasoning: str

class ScoreRequest(BaseModel):
    item_ids: List[int] = Field(..., description="List of item IDs to score")

class ScoreResponse(BaseModel):
    score: float
    item_ids: List[int]

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

@app.post("/recommend", response_model=OutfitRecommendation)
def recommend_outfit(request: RecommendRequest):
    """
    Generate outfit recommendations based on selected items, weather, and occasion
    """
    # TODO: Replace with actual ML model call
    # Example: recommendations = model.predict(selected_items, weather, occasion)

    print(f"Calling outfit generation model with context: {request.weather}, {request.occasion}")
    print(f"Selected items: {request.selected_items}")

    # Dummy logic: recommend items not in selected_items
    available_items = [item for item in DUMMY_ITEMS if item["id"] not in request.selected_items]

    # Pick 2-3 random items
    num_recommendations = min(3, len(available_items))
    recommended = random.sample(available_items, num_recommendations)

    # Generate dummy compatibility score
    compatibility_score = round(random.uniform(0.75, 0.95), 2)

    reasoning = f"Based on {request.weather} weather and {request.occasion} occasion, " \
                f"these items complement your selected pieces well."

    return OutfitRecommendation(
        recommended_items=recommended,
        compatibility_score=compatibility_score,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
