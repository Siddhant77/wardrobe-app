'use client';

import Image from 'next/image';
import { ClothingItem } from '@/types/clothing';

interface ImageCardProps {
  item: ClothingItem;
  onClick: () => void;
}

export default function ImageCard({ item, onClick }: ImageCardProps) {
  return (
    <div
      onClick={onClick}
      className="group cursor-pointer bg-white rounded-lg shadow-md overflow-hidden transition-all duration-300 hover:shadow-xl hover:scale-105"
    >
      <div className="relative aspect-square overflow-hidden bg-gray-100">
        <Image
          src={item.imagePath}
          alt={item.filename}
          fill
          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
          className="object-cover transition-transform duration-300 group-hover:scale-110"
          loading="lazy"
        />
      </div>

      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-900 truncate" title={item.filename}>
          {item.filename}
        </h3>

        {/* Placeholder for future metadata */}
        <div className="mt-2 space-y-1">
          {item.category && (
            <p className="text-xs text-gray-500">
              Category: <span className="font-medium">{item.category}</span>
            </p>
          )}
          {item.color && item.color.length > 0 && (
            <p className="text-xs text-gray-500">
              Color: <span className="font-medium">{item.color.join(', ')}</span>
            </p>
          )}
          {item.formality && (
            <p className="text-xs text-gray-500">
              Formality: <span className="font-medium">{item.formality}</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
