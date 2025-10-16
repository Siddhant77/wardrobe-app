'use client';

import Image from 'next/image';
import { useEffect } from 'react';
import { ClothingItem } from '@/types/clothing';

interface ImageModalProps {
  item: ClothingItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function ImageModal({ item, isOpen, onClose }: ImageModalProps) {
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

  if (!isOpen || !item) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4"
      onClick={onClose}
    >
      <div
        className="relative max-w-5xl max-h-[90vh] w-full bg-white rounded-lg shadow-2xl overflow-hidden"
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
        <div className="relative w-full h-[70vh] bg-gray-100">
          <Image
            src={item.imagePath}
            alt={item.filename}
            fill
            sizes="90vw"
            className="object-contain"
            priority
          />
        </div>

        {/* Metadata section */}
        <div className="p-6 border-t border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">{item.filename}</h2>

          {/* Placeholder for future metadata display */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {item.category && (
              <div>
                <p className="text-xs text-gray-500 uppercase">Category</p>
                <p className="text-sm font-medium text-gray-900">{item.category}</p>
              </div>
            )}
            {item.color && item.color.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 uppercase">Colors</p>
                <p className="text-sm font-medium text-gray-900">{item.color.join(', ')}</p>
              </div>
            )}
            {item.formality && (
              <div>
                <p className="text-xs text-gray-500 uppercase">Formality</p>
                <p className="text-sm font-medium text-gray-900">{item.formality}</p>
              </div>
            )}
            {item.season && (
              <div>
                <p className="text-xs text-gray-500 uppercase">Season</p>
                <p className="text-sm font-medium text-gray-900">{item.season}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
