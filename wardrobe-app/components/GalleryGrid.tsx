'use client';

import { useState } from 'react';
import ImageCard from './ImageCard';
import ImageModal from './ImageModal';
import { ClothingItem } from '@/types/clothing';

interface GalleryGridProps {
  items: ClothingItem[];
}

const CATEGORIES = ['tops', 'bottoms', 'outerwear', 'shoes', 'accessories'] as const;

export default function GalleryGrid({ items: initialItems }: GalleryGridProps) {
  const [items, setItems] = useState<ClothingItem[]>(initialItems);
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());

  const handleImageClick = (item: ClothingItem) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    // Delay clearing selectedItem to allow modal animation
    setTimeout(() => setSelectedItem(null), 300);
  };

  const handleItemUpdated = (updatedItem: ClothingItem) => {
    setItems(items.map(item => item.id === updatedItem.id ? updatedItem : item));
    setSelectedItem(updatedItem);
  };

  const handleItemDeleted = (itemId: string) => {
    setItems(items.filter(item => item.id !== itemId));
  };

  const handleCategoryChange = (category: string) => {
    const newCategories = new Set(selectedCategories);
    if (newCategories.has(category)) {
      newCategories.delete(category);
    } else {
      newCategories.add(category);
    }
    setSelectedCategories(newCategories);
  };

  const filteredItems = selectedCategories.size === 0
    ? items
    : items.filter(item => item.category && selectedCategories.has(item.category));

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
        <svg
          className="w-16 h-16 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No items found</h3>
        <p className="text-gray-500 max-w-md">
          Add images to the <code className="text-sm bg-gray-100 px-2 py-1 rounded">/public/wardrobe</code> folder
          to see them here.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">Filter by category:</h3>
          <span className="text-sm text-gray-600">{filteredItems.length}/{items.length}</span>
        </div>
        <div className="flex flex-wrap gap-3">
          {CATEGORIES.map((category) => (
            <label key={category} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedCategories.has(category)}
                onChange={() => handleCategoryChange(category)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-gray-700 capitalize">{category}</span>
            </label>
          ))}
        </div>
      </div>

      {filteredItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <p className="text-gray-500">No items found in selected categories</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          {filteredItems.map((item) => (
            <ImageCard key={item.id} item={item} onClick={() => handleImageClick(item)} />
          ))}
        </div>
      )}

      <ImageModal item={selectedItem} isOpen={isModalOpen} onClose={handleCloseModal} onItemUpdated={handleItemUpdated} onItemDeleted={handleItemDeleted} />
    </>
  );
}
