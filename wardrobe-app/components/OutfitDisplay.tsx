'use client';

import Image from 'next/image';
import { useState } from 'react';
import ImageModal from './ImageModal';
import { ClothingItem } from '@/types/clothing';

interface OutfitItem {
  id: string;
  name: string;
  imagePath: string;
}

interface Outfit {
  id: string;
  items: OutfitItem[];
  occasion: string;
  weather: string;
  description: string;
}

interface OutfitDisplayProps {
  outfit: Outfit;
  onGetNewOutfit: () => void;
  occasions: string[];
  weathers: string[];
  selectedOccasion: string;
  selectedWeather: string;
  onOccasionChange: (occasion: string) => void;
  onWeatherChange: (weather: string) => void;
  itemsData?: ClothingItem[]; // Full clothing item data for modal
}

export default function OutfitDisplay({
  outfit,
  onGetNewOutfit,
  occasions,
  weathers,
  selectedOccasion,
  selectedWeather,
  onOccasionChange,
  onWeatherChange,
  itemsData,
}: OutfitDisplayProps) {
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleItemClick = (outfitItem: OutfitItem) => {
    if (itemsData) {
      const fullItem = itemsData.find((item) => item.imagePath === outfitItem.imagePath);
      if (fullItem) {
        setSelectedItem(fullItem);
        setIsModalOpen(true);
      }
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setTimeout(() => setSelectedItem(null), 300);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      {/* Outfit Header */}
      <div className="mb-8">
        <div className="flex gap-12 justify-center items-start mb-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">Occasion</p>
            <select
              value={selectedOccasion}
              onChange={(e) => onOccasionChange(e.target.value)}
              className="font-semibold text-lg px-4 py-2 border border-gray-300 rounded-lg bg-white cursor-pointer hover:border-blue-500 transition-colors"
            >
              {occasions.map((occasion) => (
                <option key={occasion} value={occasion}>
                  {occasion}
                </option>
              ))}
            </select>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Weather</p>
            <select
              value={selectedWeather}
              onChange={(e) => onWeatherChange(e.target.value)}
              className="font-semibold text-lg px-4 py-2 border border-gray-300 rounded-lg bg-white cursor-pointer hover:border-blue-500 transition-colors"
            >
              {weathers.map((weather) => (
                <option key={weather} value={weather}>
                  {weather}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Outfit Items - Centered Grid */}
      <div className="flex flex-col items-center gap-8 mb-8">
        {outfit.items.map((item) => (
          <div
            key={item.id}
            onClick={() => handleItemClick(item)}
            className="cursor-pointer group"
          >
            <div className="relative bg-gray-100 rounded-lg overflow-hidden w-48 h-64 border-2 border-gray-200 group-hover:border-blue-500 transition-colors">
              <Image
                src={item.imagePath}
                alt={item.name}
                fill
                className="object-cover"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center mt-8">
        <button
          onClick={onGetNewOutfit}
          className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
        >
          New Outfit
        </button>
      </div>

      {/* Item Detail Modal */}
      <ImageModal item={selectedItem} isOpen={isModalOpen} onClose={handleCloseModal} />
    </div>
  );
}
