/**
 * TypeScript interfaces for wardrobe management system
 * Future-ready for API integration and metadata management
 */

export interface ClothingItem {
  id: string;
  filename: string;
  imagePath: string;

  // Placeholder props for future implementation
  category?: 'tops' | 'bottoms' | 'dresses' | 'outerwear' | 'shoes' | 'accessories';
  color?: string[];
  formality?: 'casual' | 'business-casual' | 'formal' | 'athletic';

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
