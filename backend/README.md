# Wardrobe Recommendation API

A dummy FastAPI backend for the wardrobe recommendation system. This includes endpoints for querying items, generating outfit recommendations, and scoring outfit compatibility.

## Setup

### Prerequisites
- Python 3.9+
- pip

### Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the development server with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at: `http://localhost:8000`

Interactive API documentation (Swagger UI): `http://localhost:8000/docs`

Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### 1. Get All Items
**GET** `/items`

Returns all wardrobe items from the dummy database.

**Example:**
```bash
curl http://localhost:8000/items
```

**Response:**
```json
[
  {
    "id": 1,
    "category": "tops",
    "color": "white",
    "formality": "business-casual",
    "name": "White Oxford Shirt",
    "image_path": "/wardrobe/shirt_1.jpg"
  },
  ...
]
```

### 2. Get Specific Item
**GET** `/items/{item_id}`

Returns a specific wardrobe item by ID.

**Example:**
```bash
curl http://localhost:8000/items/1
```

**Response:**
```json
{
  "id": 1,
  "category": "tops",
  "color": "white",
  "formality": "business-casual",
  "name": "White Oxford Shirt",
  "image_path": "/wardrobe/shirt_1.jpg"
}
```

### 3. Get Outfit Recommendations
**POST** `/recommend`

Generate outfit recommendations based on selected items, weather, and occasion.

**Example:**
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "selected_items": [1, 2],
    "weather": "cold",
    "occasion": "work"
  }'
```

**Response:**
```json
{
  "recommended_items": [
    {
      "id": 3,
      "category": "outerwear",
      "color": "black",
      "formality": "formal",
      "name": "Black Blazer",
      "image_path": "/wardrobe/blazer_1.jpg"
    },
    ...
  ],
  "compatibility_score": 0.87,
  "reasoning": "Based on cold weather and work occasion, these items complement your selected pieces well."
}
```

### 4. Score Outfit Compatibility
**POST** `/score`

Score the compatibility of a set of items.

**Example:**
```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": [1, 2, 3]
  }'
```

**Response:**
```json
{
  "score": 0.82,
  "item_ids": [1, 2, 3]
}
```

## Terminal Output

The API prints debug information to the terminal for each operation:

- `GET /items` → "Querying database for items..."
- `GET /items/{item_id}` → "Fetching item {item_id} from database..."
- `POST /recommend` → "Calling outfit generation model with context: {weather}, {occasion}"
- `POST /score` → "Calling compatibility scoring model for items: {item_ids}"

## Code Structure

```
backend/
├── main.py              # FastAPI application with all endpoints
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Key Components in `main.py`:

1. **Pydantic Models** - Request/response validation:
   - `ClothingItem` - Wardrobe item structure
   - `RecommendRequest` - Recommendation request body
   - `OutfitRecommendation` - Recommendation response
   - `ScoreRequest` - Scoring request body
   - `ScoreResponse` - Scoring response

2. **CORS Middleware** - Allows frontend (localhost:3000) to make requests

3. **Dummy Database** - `DUMMY_ITEMS` list simulating database storage

4. **TODO Comments** - Placeholders for:
   - Real database queries (PostgreSQL, MongoDB, etc.)
   - ML model calls (outfit generation, compatibility scoring)

## Future Implementation

### Database Integration
Replace `DUMMY_ITEMS` with real database queries:
```python
# TODO: Replace with actual database query
# Example: items = db.query(ClothingItem).all()
```

### ML Model Integration
Replace dummy logic with actual ML models:
```python
# TODO: Replace with actual ML model call
# Example: recommendations = model.predict(selected_items, weather, occasion)
# Example: score = compatibility_model.score(item_ids)
```

## Testing

You can test all endpoints interactively using:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- curl commands (see examples above)
- Any HTTP client (Postman, Insomnia, etc.)

## CORS Configuration

The API is configured to accept requests from `http://localhost:3000` (Next.js frontend). To add more origins, update the `allow_origins` list in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    ...
)
```
