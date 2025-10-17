/**
 * TypeScript types for FastAPI backend responses
 */

export interface APIClothingItem {
  id: number;
  category: string;
  color: string;
  formality: string;
  name?: string;
  image_path?: string;
}

export interface ScoreRequest {
  item_ids: number[];
}

export interface ScoreResponse {
  score: number;
  item_ids: number[];
}
