'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import OutfitDisplay from '@/components/OutfitDisplay';
import { OutfitRecommendation, RecommendRequest } from '@/types/api';
import { ClothingItem } from '@/types/clothing';
import { logDebug, logError } from '@/lib/logger';

const API_BASE_URL = 'http://localhost:8000';

const OCCASIONS = ['casual', 'formal', 'sports', 'party'];
const WEATHERS = ['cold', 'hot', 'rainy'];

export default function OutfitPage() {
  const [outfitRecommendation, setOutfitRecommendation] = useState<OutfitRecommendation | null>(null);
  const [currentOutfitIndex, setCurrentOutfitIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOccasion, setSelectedOccasion] = useState('casual');
  const [selectedWeather, setSelectedWeather] = useState('mild');
  const [wardrobeItems, setWardrobeItems] = useState<ClothingItem[]>([]);

  // Load wardrobe items on mount
  useEffect(() => {
    const loadWardrobeItems = async () => {
      try {
        const response = await fetch('/api/wardrobe');
        if (response.ok) {
          const items: ClothingItem[] = await response.json();
          logDebug('Loaded wardrobeItems:', items);
          logDebug('First item category:', items[0]?.category);
          setWardrobeItems(items);
        } else {
          logError('API returned non-ok status:', response.status.toString());
        }
      } catch (err) {
        logError('Failed to load wardrobe items:', err);
      }
    };
    loadWardrobeItems();
  }, []);

  const fetchOutfitRecommendation = async () => {
    setLoading(true);
    setError(null);
    try {
      const recommendRequest: RecommendRequest = {
        selected_items: [],
        weather: selectedWeather,
        occasion: selectedOccasion,
      };

      const response = await fetch(`${API_BASE_URL}/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(recommendRequest),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data: OutfitRecommendation = await response.json();
      setOutfitRecommendation(data);
      setCurrentOutfitIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch outfit recommendation');
      logError('Error fetching outfit:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVoteOutfit = async (voteValue: number) => {
    if (!outfitRecommendation || outfitRecommendation.recommended_outfits.length === 0) {
      return;
    }

    const currentOutfit = outfitRecommendation.recommended_outfits[currentOutfitIndex];
    const itemIds = currentOutfit.items.map((item) => item.id);

    try {
      const response = await fetch(`${API_BASE_URL}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_ids: itemIds,
          vote: voteValue,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      logDebug('Vote recorded:', data);
      alert(data.message);
    } catch (err) {
      logError('Error recording vote:', err);
      alert('Failed to record vote');
    }
  };

  useEffect(() => {
    fetchOutfitRecommendation();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="w-full max-w-4xl">
        <Link
          href="/"
          className="inline-block mb-8 text-blue-600 hover:text-blue-700 transition-colors"
        >
          ← Back to Home
        </Link>

        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-6">Outfit Recommendation</h1>
          {outfitRecommendation && outfitRecommendation.recommended_outfits.length > 0 && (
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => handleVoteOutfit(1)}
                className="flex items-center gap-2 px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                👍 Like
              </button>
              <button
                onClick={() => handleVoteOutfit(-1)}
                className="flex items-center gap-2 px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                👎 Dislike
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <p className="text-gray-500">Loading outfit recommendation...</p>
          </div>
        ) : error ? (
          <div className="text-center">
            <p className="text-red-500">Error: {error}</p>
          </div>
        ) : outfitRecommendation && outfitRecommendation.recommended_outfits.length > 0 ? (
          <div className="space-y-8">
            {/* Outfit Navigation */}
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={() => setCurrentOutfitIndex(Math.max(0, currentOutfitIndex - 1))}
                disabled={currentOutfitIndex === 0}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
              >
                ← Previous
              </button>
              <span className="text-gray-600">
                Outfit {currentOutfitIndex + 1} of {outfitRecommendation.recommended_outfits.length}
              </span>
              <button
                onClick={() =>
                  setCurrentOutfitIndex(
                    Math.min(
                      outfitRecommendation.recommended_outfits.length - 1,
                      currentOutfitIndex + 1
                    )
                  )
                }
                disabled={currentOutfitIndex === outfitRecommendation.recommended_outfits.length - 1}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
              >
                Next →
              </button>
            </div>

            {/* Score Display */}
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-700">
                Outfit Score:{' '}
                <span className="text-blue-600">
                  {outfitRecommendation.recommended_outfits[currentOutfitIndex].score.toFixed(4)}
                </span>
              </p>
            </div>

            {/* Current Outfit Display */}
            <OutfitDisplay
              outfit={{
                id: `outfit-${currentOutfitIndex}`,
                items: outfitRecommendation.recommended_outfits[currentOutfitIndex].items.map(
                  (item) => ({
                    id: item.id.toString(),
                    name: item.name || item.category,
                    imagePath: item.image_path || '',
                  })
                ),
                occasion: selectedOccasion,
                weather: selectedWeather,
                description: outfitRecommendation.reasoning,
              }}
              onGetNewOutfit={fetchOutfitRecommendation}
              occasions={OCCASIONS}
              weathers={WEATHERS}
              selectedOccasion={selectedOccasion}
              selectedWeather={selectedWeather}
              onOccasionChange={setSelectedOccasion}
              onWeatherChange={setSelectedWeather}
              itemsData={wardrobeItems}
            />
          </div>
        ) : (
          <div className="text-center">
            <p className="text-gray-500">No outfit recommendation available</p>
          </div>
        )}
      </div>
    </main>
  );
}
