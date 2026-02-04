'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import GalleryGrid from '@/components/GalleryGrid';
import ImageUpload from '@/components/ImageUpload';
import { ClothingItem } from '@/types/clothing';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function WardrobePage() {
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        // Call backend API directly
        const response = await fetch(`${API_BASE_URL}/items`);

        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        // Transform backend response to match ClothingItem type
        const transformedItems: ClothingItem[] = data.map((item: any) => ({
          id: item.id.toString(),
          filename: item.image_name,
          imagePath: item.image_url,
          category: item.category.toLowerCase(),
          weatherLabel: item.weather_label,
          formalityLabel: item.formality_label,
        }));

        setItems(transformedItems);
      } catch (err) {
        console.error('Failed to load wardrobe items:', err);
        setError(err instanceof Error ? err.message : 'Failed to load items');
        setItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Loading wardrobe items...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <Link
              href="/"
              className="inline-block mb-4 text-blue-600 hover:text-blue-700 transition-colors"
            >
              ← Back to Home
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">My Wardrobe</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-red-500">Error: {error}</p>
            <p className="text-gray-600 mt-2">Make sure the backend is running at {API_BASE_URL}</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            href="/"
            className="inline-block mb-4 text-blue-600 hover:text-blue-700 transition-colors"
          >
            ← Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">My Wardrobe</h1>
          <p className="mt-2 text-sm text-gray-600">
            {items.length} {items.length === 1 ? 'item' : 'items'} in your collection
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {items.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No items in your wardrobe yet.</p>
            <p className="text-sm text-gray-400">Upload images below or run the migration script to import existing data.</p>
          </div>
        ) : (
          <GalleryGrid items={items} />
        )}

        {/* Upload section */}
        <div className="mt-16 pt-8 border-t border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload New Item</h2>
          <div className="max-w-2xl">
            <ImageUpload />
          </div>
        </div>
      </main>
    </div>
  );
}
