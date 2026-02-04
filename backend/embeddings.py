"""
Embeddings and label classification helper functions.

This module provides functions to:
1. Generate CLIP ViT-B/32 embeddings for clothing images and save to vit_embeddings.npy
2. Generate FashionCLIP embeddings for clothing images and save to fashion_embeddings.npy
3. Classify weather labels using cosine similarity
4. Classify formality labels using cosine similarity
5. Compute category centroids from training data and save to category_centroids.npz
6. Classify clothing category for new images using centroid-based matching
"""

import torch
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Dict, Tuple
import clip
from fashion_clip.fashion_clip import FashionCLIP
from logger import log_debug, log_error, log_warning


# Initialize models (loaded once at module level for efficiency)
_clip_model = None
_clip_preprocess = None
_fashion_clip_model = None
_device = None
_weather_label_embeddings = None
_formality_label_embeddings = None


def _get_device() -> str:
    """Determine the best available device for inference."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def _get_clip_model(device: str) -> Tuple:
    """Load CLIP model (cached on first call)."""
    global _clip_model, _clip_preprocess
    if _clip_model is None:
        try:
            _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=device)
            log_debug("Loaded CLIP ViT-B/32 model")
        except Exception as e:
            log_error("Failed to load CLIP model", exception=e)
            raise
    return _clip_model, _clip_preprocess


def _get_fashion_clip_model() -> FashionCLIP:
    """Load FashionCLIP model (cached on first call)."""
    global _fashion_clip_model
    if _fashion_clip_model is None:
        try:
            _fashion_clip_model = FashionCLIP(model_name='fashion-clip', token=None)
            log_debug("Loaded FashionCLIP model")
        except Exception as e:
            log_error("Failed to load FashionCLIP model", exception=e)
            raise
    return _fashion_clip_model


def _load_embeddings_array(embeddings_path: Path, num_items: int) -> np.ndarray:
    """
    Load embeddings array from file, or create new if doesn't exist.

    Args:
        embeddings_path: Path to the .npy file
        num_items: Expected number of items (rows) in embeddings

    Returns:
        Numpy array of shape (num_items, 512) with dtype float32
    """
    log_debug(f"Loading embeddings from {embeddings_path}, num_items={num_items}")
    if embeddings_path.exists():
        try:
            embeddings = np.load(embeddings_path)
            if embeddings.shape[0] != num_items or embeddings.shape[1] != 512:
                if embeddings.shape[1] != 512:
                    # Invalid embedding dimension - fatal error
                    log_error(
                        f"Embeddings file has invalid embedding dimension {embeddings.shape[1]}, "
                        f"expected 512. Creating new array."
                    )
                    return np.zeros((num_items, 512), dtype=np.float32)

                # Row count mismatch - pad with zeros
                if embeddings.shape[0] < num_items:
                    padding = np.zeros((num_items - embeddings.shape[0], 512), dtype=np.float32)
                    result = np.vstack([embeddings.astype(np.float32), padding])
                    log_warning(
                        f"Embeddings file has {embeddings.shape[0]} rows, expected {num_items}. "
                        f"Padding with {num_items - embeddings.shape[0]} zero rows."
                    )
                    return result
                else:
                    # Truncate if larger
                    log_warning(
                        f"Embeddings file has {embeddings.shape[0]} rows, expected {num_items}. "
                        f"Truncating to {num_items} rows."
                    )
                    return embeddings[:num_items].astype(np.float32)
            return embeddings.astype(np.float32)
        except Exception as e:
            log_error(f"Failed to load embeddings from {embeddings_path}", exception=e)
            return np.zeros((num_items, 512), dtype=np.float32)
    else:
        return np.zeros((num_items, 512), dtype=np.float32)


def _save_embeddings_array(embeddings_path: Path, embeddings: np.ndarray) -> None:
    """
    Save embeddings array to file.

    Args:
        embeddings_path: Path to save the .npy file
        embeddings: Numpy array of embeddings to save
    """
    try:
        embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(embeddings_path, embeddings.astype(np.float32))
        log_debug(f"Saved embeddings to {embeddings_path}")
    except Exception as e:
        log_error(f"Failed to save embeddings to {embeddings_path}", exception=e)
        raise


def save_item_embeddings(item_id: int, clip_embedding: np.ndarray, fashion_embedding: np.ndarray, embeddings_dir: str = None) -> None:
    """
    Save CLIP and FashionCLIP embeddings for an item to disk.
    Called after metadata.csv is updated to ensure array sizing is correct.

    Args:
        item_id: ID of the item
        clip_embedding: 512-dimensional CLIP embedding
        fashion_embedding: 512-dimensional FashionCLIP embedding
        embeddings_dir: Directory containing .npy files (default: ../wardrobe-app/public)

    Raises:
        Exception: If embeddings cannot be saved
    """
    if embeddings_dir is None:
        embeddings_dir = "../wardrobe-app/public"

    embeddings_dir = Path(embeddings_dir)
    metadata_path = embeddings_dir / "metadata.csv"

    if not metadata_path.exists():
        log_warning(f"Metadata file not found at {metadata_path}, skipping embedding save")
        return

    try:
        # Count items in updated metadata to determine array size
        with open(metadata_path, 'r') as f:
            num_items = sum(1 for _ in f) - 1  # -1 for header

        # Save CLIP embedding
        vit_path = embeddings_dir / "vit_embeddings.npy"
        vit_embeddings = _load_embeddings_array(vit_path, num_items)
        vit_embeddings[item_id - 1] = clip_embedding
        _save_embeddings_array(vit_path, vit_embeddings)
        log_debug(f"Saved CLIP embedding for item {item_id}")

        # Save FashionCLIP embedding
        fashion_path = embeddings_dir / "fashion_embeddings.npy"
        fashion_embeddings = _load_embeddings_array(fashion_path, num_items)
        fashion_embeddings[item_id - 1] = fashion_embedding
        _save_embeddings_array(fashion_path, fashion_embeddings)
        log_debug(f"Saved FashionCLIP embedding for item {item_id}")

        # Log updated sizes
        log_debug(f"Data state after add: metadata.csv={num_items} rows, vit_embeddings={vit_embeddings.shape[0]} rows, fashion_embeddings={fashion_embeddings.shape[0]} rows")

    except Exception as e:
        log_error(f"Failed to save embeddings for item {item_id}", exception=e)
        raise


def generate_clip_embedding(image_path: str, item_id: int = None, embeddings_dir: str = None, device: str = None) -> np.ndarray:
    """
    Generate a CLIP ViT-B/32 embedding for an image.

    Args:
        image_path: Path to the image file
        item_id: Unused (for API compatibility)
        embeddings_dir: Unused (for API compatibility)
        device: Device to use ('cuda', 'mps', 'cpu'). Auto-detected if None.

    Returns:
        512-dimensional normalized embedding as numpy array (float32)

    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If image loading or embedding generation fails
    """
    if device is None:
        device = _get_device()

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        # Load and preprocess image
        img = Image.open(image_path).convert("RGB")
        model, preprocess = _get_clip_model(device)
        img_tensor = preprocess(img).unsqueeze(0).to(device)

        # Generate embedding
        with torch.no_grad():
            image_embedding = model.encode_image(img_tensor)
            # Normalize to unit norm
            image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)

        embedding = image_embedding.cpu().numpy().astype(np.float32).squeeze()
        return embedding

    except FileNotFoundError:
        raise
    except Exception as e:
        log_error(f"Failed to generate CLIP embedding for {image_path.name}", exception=e)
        raise


def generate_fashion_embedding(image_path: str, item_id: int = None, embeddings_dir: str = None) -> np.ndarray:
    """
    Generate a FashionCLIP embedding for an image.

    Args:
        image_path: Path to the image file
        item_id: Unused (for API compatibility)
        embeddings_dir: Unused (for API compatibility)

    Returns:
        512-dimensional normalized embedding as numpy array (float32)

    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If image loading or embedding generation fails
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        model = _get_fashion_clip_model()

        # FashionCLIP's encode_images expects a list of paths
        with torch.no_grad():
            embeddings = model.encode_images([str(image_path)], batch_size=1)
            # Normalize to unit norm
            embeddings = embeddings / np.linalg.norm(embeddings, ord=2, axis=-1, keepdims=True)

        embedding = embeddings[0].astype(np.float32)
        return embedding

    except FileNotFoundError:
        raise
    except Exception as e:
        log_error(f"Failed to generate FashionCLIP embedding for {image_path.name}", exception=e)
        raise


def _get_weather_label_embeddings(device: str = None) -> Dict[str, np.ndarray]:
    """
    Get or generate CLIP embeddings for weather labels.

    Returns a cached dictionary mapping label names to embeddings.
    """
    global _weather_label_embeddings

    if _weather_label_embeddings is not None:
        return _weather_label_embeddings

    if device is None:
        device = _get_device()

    try:
        model, _ = _get_clip_model(device)

        label_texts = {
            'HOT': 'hot weather clothing',
            'COLD': 'cold weather clothing',
            'RAINY': 'rainy weather clothing'
        }

        _weather_label_embeddings = {}
        for label_name, label_text in label_texts.items():
            with torch.no_grad():
                text_tokens = clip.tokenize(label_text).to(device)
                text_embedding = model.encode_text(text_tokens)
                # Normalize
                text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            _weather_label_embeddings[label_name] = text_embedding.cpu().numpy().astype(np.float32).squeeze()

        log_debug(f"Loaded embeddings for {len(_weather_label_embeddings)} weather labels")
        return _weather_label_embeddings

    except Exception as e:
        log_error("Failed to generate weather label embeddings", exception=e)
        raise


def _get_formality_label_embeddings(device: str = None) -> Dict[str, np.ndarray]:
    """
    Get or generate CLIP embeddings for formality labels.

    Returns a cached dictionary mapping label names to embeddings.
    """
    global _formality_label_embeddings

    if _formality_label_embeddings is not None:
        return _formality_label_embeddings

    if device is None:
        device = _get_device()

    try:
        model, _ = _get_clip_model(device)

        label_texts = {
            'CASUAL': 'lounging wear',
            'FORMAL': 'formal wear',
            'SPORTS': 'exercise clothes',
            'PARTY': 'party wear'
        }

        _formality_label_embeddings = {}
        for label_name, label_text in label_texts.items():
            with torch.no_grad():
                text_tokens = clip.tokenize(label_text).to(device)
                text_embedding = model.encode_text(text_tokens)
                # Normalize
                text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            _formality_label_embeddings[label_name] = text_embedding.cpu().numpy().astype(np.float32).squeeze()

        log_debug(f"Loaded embeddings for {len(_formality_label_embeddings)} formality labels")
        return _formality_label_embeddings

    except Exception as e:
        log_error("Failed to generate formality label embeddings", exception=e)
        raise


def classify_weather_labels(image_embedding: np.ndarray, threshold: float = 0.24) -> int:
    """
    Classify weather labels for an image using cosine similarity.

    Args:
        image_embedding: 512-dimensional CLIP embedding (normalized)
        threshold: Similarity threshold for label assignment (default 0.24)

    Returns:
        Bitmask integer representing weather labels:
        - 0b0001 (1): Hot
        - 0b0010 (2): Cold
        - 0b0100 (4): Rainy
        - Can combine: 3=Hot+Cold, 5=Hot+Rainy, 6=Cold+Rainy, 7=All three

    Example:
        embedding = generate_clip_embedding("image.jpg")
        labels = classify_weather_labels(embedding)
        # labels might be 6 (binary 0110 = Cold + Rainy)
    """
    weather_map = {
        'HOT': 0b0001,
        'COLD': 0b0010,
        'RAINY': 0b0100,
    }

    try:
        label_embeddings = _get_weather_label_embeddings()

        label_value = 0
        for label_name, label_embedding in label_embeddings.items():
            # Cosine similarity (dot product for normalized embeddings)
            similarity = np.dot(image_embedding, label_embedding)

            if similarity >= threshold:
                label_value |= weather_map[label_name]

        return label_value

    except Exception as e:
        log_error(f"Failed to classify weather labels", exception=e)
        return 0


def delete_item_embeddings(item_id: int, embeddings_dir: str = None) -> None:
    """
    Delete embeddings for an item from both vit_embeddings.npy and fashion_embeddings.npy.

    Removes the row at index (item_id - 1) by shifting all subsequent rows up.
    Updates both .npy files atomically.

    Args:
        item_id: ID of the item to remove embeddings for
        embeddings_dir: Directory containing .npy files (default: ../wardrobe-app/public)

    Raises:
        Exception: If embeddings files cannot be accessed or modified
    """
    if embeddings_dir is None:
        embeddings_dir = "../wardrobe-app/public"

    embeddings_dir = Path(embeddings_dir)
    vit_path = embeddings_dir / "vit_embeddings.npy"
    fashion_path = embeddings_dir / "fashion_embeddings.npy"

    try:
        vit_size_after = None
        fashion_size_after = None

        # Delete from vit_embeddings.npy
        if vit_path.exists():
            try:
                embeddings = np.load(vit_path)
                if embeddings.shape[0] > item_id - 1:
                    # Remove row at index (item_id - 1)
                    embeddings = np.delete(embeddings, item_id - 1, axis=0)
                    _save_embeddings_array(vit_path, embeddings)
                    vit_size_after = embeddings.shape[0]
                    log_debug(f"Deleted embedding for item {item_id} from {vit_path}")
            except Exception as e:
                log_error(f"Failed to delete embedding from {vit_path}", exception=e)
        else:
            log_warning(f"vit_embeddings.npy not found at {vit_path}")

        # Delete from fashion_embeddings.npy
        if fashion_path.exists():
            try:
                embeddings = np.load(fashion_path)
                if embeddings.shape[0] > item_id - 1:
                    # Remove row at index (item_id - 1)
                    embeddings = np.delete(embeddings, item_id - 1, axis=0)
                    _save_embeddings_array(fashion_path, embeddings)
                    fashion_size_after = embeddings.shape[0]
                    log_debug(f"Deleted embedding for item {item_id} from {fashion_path}")
            except Exception as e:
                log_error(f"Failed to delete embedding from {fashion_path}", exception=e)
        else:
            log_warning(f"fashion_embeddings.npy not found at {fashion_path}")

        # Log updated sizes
        log_debug(f"Data state after delete: vit_embeddings={vit_size_after} rows, fashion_embeddings={fashion_size_after} rows")

    except Exception as e:
        log_error(f"Error deleting embeddings for item {item_id}", exception=e)
        raise


def classify_formality_labels(image_embedding: np.ndarray, threshold: float = 0.23) -> int:
    """
    Classify formality labels for an image using cosine similarity.

    Args:
        image_embedding: 512-dimensional CLIP embedding (normalized)
        threshold: Similarity threshold for label assignment (default 0.23)

    Returns:
        Bitmask integer representing formality labels:
        - 0b0001 (1): Casual
        - 0b0010 (2): Formal
        - 0b0100 (4): Sports
        - 0b1000 (8): Party
        - Can combine: 3=Casual+Formal, 5=Casual+Sports, etc.

    Example:
        embedding = generate_clip_embedding("image.jpg")
        labels = classify_formality_labels(embedding)
        # labels might be 5 (binary 0101 = Casual + Sports)
    """
    formality_map = {
        'CASUAL': 0b0001,
        'FORMAL': 0b0010,
        'SPORTS': 0b0100,
        'PARTY': 0b1000,
    }

    try:
        label_embeddings = _get_formality_label_embeddings()

        label_value = 0
        for label_name, label_embedding in label_embeddings.items():
            # Cosine similarity (dot product for normalized embeddings)
            similarity = np.dot(image_embedding, label_embedding)

            if similarity >= threshold:
                label_value |= formality_map[label_name]

        return label_value

    except Exception as e:
        log_error(f"Failed to classify formality labels", exception=e)
        return 0


def compute_category_centroids(embeddings_array: np.ndarray, metadata_df, embeddings_dir: str = None) -> Dict[str, np.ndarray]:
    """
    Compute centroid (mean embedding) for each category using FashionCLIP embeddings.

    Args:
        embeddings_array: Numpy array of shape (num_items, 512) with FashionCLIP embeddings
        metadata_df: Pandas DataFrame with metadata (must have 'item_category' column)
        embeddings_dir: Directory to save centroids (default: ../wardrobe-app/public)

    Returns:
        Dictionary mapping category names to centroid embeddings (512-dim numpy arrays)

    Raises:
        ValueError: If embeddings_array shape doesn't match metadata_df length
    """
    if embeddings_array.shape[0] != len(metadata_df):
        raise ValueError(
            f"Embeddings array has {embeddings_array.shape[0]} rows "
            f"but metadata has {len(metadata_df)} rows"
        )

    if embeddings_dir is None:
        embeddings_dir = "../wardrobe-app/public"

    try:
        centroids = {}

        # Group by category and compute mean embedding
        for category in metadata_df['item_category'].unique():
            category_mask = metadata_df['item_category'] == category
            category_embeddings = embeddings_array[category_mask]

            # Compute mean embedding (centroid)
            centroid = np.mean(category_embeddings, axis=0)
            # Normalize to unit norm
            centroid = centroid / np.linalg.norm(centroid, ord=2)
            centroids[category] = centroid.astype(np.float32)

            log_debug(f"Computed centroid for category '{category}' with {len(category_embeddings)} items")

        # Save centroids to file
        centroids_path = Path(embeddings_dir) / "category_centroids.npz"
        centroids_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as npz (supports dictionary of arrays)
        np.savez(centroids_path, **centroids)
        log_debug(f"Saved {len(centroids)} category centroids to {centroids_path}")

        return centroids

    except Exception as e:
        log_error(f"Failed to compute category centroids", exception=e)
        raise


def load_category_centroids(embeddings_dir: str = None) -> Dict[str, np.ndarray]:
    """
    Load pre-computed category centroids from file.

    Args:
        embeddings_dir: Directory containing category_centroids.npz (default: ../wardrobe-app/public)

    Returns:
        Dictionary mapping category names to centroid embeddings (512-dim numpy arrays)
        Returns empty dict if file doesn't exist

    Raises:
        Exception: If centroids file cannot be loaded
    """
    if embeddings_dir is None:
        embeddings_dir = "../wardrobe-app/public"

    centroids_path = Path(embeddings_dir) / "category_centroids.npz"

    if not centroids_path.exists():
        log_warning(f"Category centroids file not found at {centroids_path}")
        return {}

    try:
        # Load npz file and convert to dict
        centroids_file = np.load(centroids_path)
        centroids = {name: centroids_file[name].astype(np.float32) for name in centroids_file.files}
        log_debug(f"Loaded {len(centroids)} category centroids from {centroids_path}")
        return centroids

    except Exception as e:
        log_error(f"Failed to load category centroids from {centroids_path}", exception=e)
        return {}


def classify_category(image_embedding: np.ndarray, centroids: Dict[str, np.ndarray], threshold: float = 0.25) -> str:
    """
    Classify an image to the nearest category based on cosine similarity to centroids.

    Args:
        image_embedding: 512-dimensional FashionCLIP embedding (normalized)
        centroids: Dictionary mapping category names to centroid embeddings
        threshold: Minimum similarity threshold (default 0.25). If no category exceeds threshold,
                   returns 'unknown'

    Returns:
        Category name (string) with highest cosine similarity to image embedding.
        Returns 'unknown' if centroids is empty or no category exceeds threshold.

    Example:
        centroids = load_category_centroids()
        fashion_emb = generate_fashion_embedding("image.jpg")
        category = classify_category(fashion_emb, centroids)
        # Returns 'tops', 'bottoms', etc.
    """
    if not centroids:
        log_warning("No centroids available for category classification")
        return "unknown"

    try:
        best_category = "unknown"
        best_similarity = threshold - 0.01  # Start below threshold to enforce it

        for category_name, centroid in centroids.items():
            # Cosine similarity (dot product for normalized embeddings)
            similarity = np.dot(image_embedding, centroid)

            if similarity > best_similarity:
                best_similarity = similarity
                best_category = category_name

        log_debug(f"Classified image to '{best_category}' with similarity {best_similarity:.4f}")
        return best_category

    except Exception as e:
        log_error(f"Failed to classify category", exception=e)
        return "unknown"
