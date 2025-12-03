'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';
import { ClothingItem } from '@/types/clothing';

interface ImageModalProps {
  item: ClothingItem | null;
  isOpen: boolean;
  onClose: () => void;
}

// Decode binary labels to strings
const WEATHER_LABELS = {
  0b0001: 'Hot',
  0b0010: 'Cold',
  0b0100: 'Rainy',
};

const FORMALITY_LABELS = {
  0b0001: 'Casual',
  0b0010: 'Formal',
  0b0100: 'Sports',
  0b1000: 'Party',
};

function decodeBinaryLabels(value: number | undefined, labelMap: Record<number, string>): string[] {
  if (value === undefined || value === 0) return [];

  const labels: string[] = [];
  Object.entries(labelMap).forEach(([bitValue, label]) => {
    const bit = parseInt(bitValue, 10);
    if ((value & bit) === bit) {
      labels.push(label);
    }
  });
  return labels;
}

export default function ImageModal({ item, isOpen, onClose }: ImageModalProps) {
  const [selectedCategory, setSelectedCategory] = useState(item?.category || '');
  const [selectedWeatherLabels, setSelectedWeatherLabels] = useState<string[]>(
    item?.weatherLabel ? decodeBinaryLabels(item.weatherLabel, WEATHER_LABELS) : []
  );
  const [selectedFormalityLabels, setSelectedFormalityLabels] = useState<string[]>(
    item?.formalityLabel ? decodeBinaryLabels(item.formalityLabel, FORMALITY_LABELS) : []
  );

  const categories = [
    'tops',
    'bottoms',
    'dresses',
    'outerwear',
    'shoes',
    'accessories',
  ];

  const weatherOptions = Object.values(WEATHER_LABELS);
  const formalityOptions = Object.values(FORMALITY_LABELS);

  const toggleWeatherLabel = (label: string) => {
    setSelectedWeatherLabels((prev: string[]) =>
      prev.includes(label) ? prev.filter((l: string) => l !== label) : [...prev, label]
    );
  };

  const toggleFormalityLabel = (label: string) => {
    setSelectedFormalityLabels((prev: string[]) =>
      prev.includes(label) ? prev.filter((l: string) => l !== label) : [...prev, label]
    );
  };

  // Close modal on ESC key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Update state when item changes
  useEffect(() => {
    if (item) {
      console.log('ImageModal item:', item);
      setSelectedCategory((item.category || '').toLowerCase());
      setSelectedWeatherLabels(
        item.weatherLabel ? decodeBinaryLabels(item.weatherLabel, WEATHER_LABELS) : []
      );
      setSelectedFormalityLabels(
        item.formalityLabel ? decodeBinaryLabels(item.formalityLabel, FORMALITY_LABELS) : []
      );
    }
  }, [item]);

  // Print all selected values whenever they change
  useEffect(() => {
    console.log('All selected values:', {
      selectedCategory,
      selectedWeatherLabels,
      selectedFormalityLabels,
    });
  }, [selectedCategory, selectedWeatherLabels, selectedFormalityLabels]);

  if (!isOpen || !item) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4"
      onClick={onClose}
    >
      <div
        className="relative max-w-5xl max-h-[90vh] w-full bg-white rounded-lg shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition-colors"
          aria-label="Close modal"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-gray-700"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Image container */}
        <div className="relative w-full h-[50vh] bg-gray-100 flex-shrink-0">
          <Image
            src={item.imagePath}
            alt={item.filename}
            fill
            sizes="90vw"
            className="object-contain"
            priority
          />
        </div>

        {/* Metadata section - scrollable */}
        <div className="p-6 border-t border-gray-200 overflow-y-auto flex-1">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">{item.filename}</h2>

          <div className="space-y-6">
            {/* Category Dropdown */}
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => {
                  console.log('Dropdown changed to:', e.target.value);
                  console.log('Available options:', categories);
                  console.log('Does selectedCategory match any option?', categories.includes(selectedCategory));
                  setSelectedCategory(e.target.value);
                }}
                className="w-full md:w-1/2 px-4 py-2 border border-gray-300 rounded-lg bg-white cursor-pointer hover:border-blue-500 transition-colors"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
              {/* <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                Debug: selectedCategory="{selectedCategory}" | categories={JSON.stringify(categories)}
              </div> */}
            </div>

            {/* Weather Labels - Selectable Boxes */}
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-3">
                Weather Labels
              </label>
              <div className="flex flex-wrap gap-2">
                {weatherOptions.map((label) => (
                  <button
                    key={label}
                    onClick={() => toggleWeatherLabel(label)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      selectedWeatherLabels.includes(label)
                        ? 'bg-blue-500 text-white border-2 border-blue-600'
                        : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:border-blue-400'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Formality Labels - Selectable Boxes */}
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-3">
                Formality Labels
              </label>
              <div className="flex flex-wrap gap-2">
                {formalityOptions.map((label) => (
                  <button
                    key={label}
                    onClick={() => toggleFormalityLabel(label)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      selectedFormalityLabels.includes(label)
                        ? 'bg-blue-500 text-white border-2 border-blue-600'
                        : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:border-blue-400'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Display selected values summary */}
            {('color' in item && item.color) || ('season' in item && item.season) ? (
              <div className="mt-6 pt-6 border-t border-gray-200">
                {'color' in item && item.color && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 uppercase mb-2">Colors</p>
                    <p className="text-sm font-medium text-gray-900">
                      {Array.isArray(item.color) ? item.color.join(', ') : item.color}
                    </p>
                  </div>
                )}
                {'season' in item && item.season && (
                  <div>
                    <p className="text-xs text-gray-500 uppercase mb-2">Season</p>
                    <p className="text-sm font-medium text-gray-900">{item.season}</p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
