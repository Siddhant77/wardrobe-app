'use client';

import { useState } from 'react';
import ImageCard from './ImageCard';
import ImageModal from './ImageModal';
import { ClothingItem } from '@/types/clothing';

interface GalleryGridProps {
  items: ClothingItem[];
}

export default function GalleryGrid({ items }: GalleryGridProps) {
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleImageClick = (item: ClothingItem) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    // Delay clearing selectedItem to allow modal animation
    setTimeout(() => setSelectedItem(null), 300);
  };

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
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
        {items.map((item) => (
          <ImageCard key={item.id} item={item} onClick={() => handleImageClick(item)} />
        ))}
      </div>

      <ImageModal item={selectedItem} isOpen={isModalOpen} onClose={handleCloseModal} />
    </>
  );
}
