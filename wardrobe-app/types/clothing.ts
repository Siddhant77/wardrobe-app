export interface ClothingItem {
  id: string;
  filename: string;
  imagePath: string;

  // Placeholder props for future implementation
  category?: 'tops' | 'bottoms' | 'dresses' | 'outerwear' | 'shoes' | 'accessories';
  color?: string[];
  formality?: 'casual' | 'business-casual' | 'formal' | 'athletic';

  // Binary label metadata (decoded to strings in modal)
  weatherLabel?: number;
  formalityLabel?: number;

  // Additional metadata placeholders
  season?: 'spring' | 'summer' | 'fall' | 'winter' | 'all-season';
  brand?: string;
  dateAdded?: Date;
  lastWorn?: Date;
  tags?: string[];
}

export interface GalleryFilters {
  category?: string;
  color?: string;
  formality?: string;
  searchQuery?: string;
}
