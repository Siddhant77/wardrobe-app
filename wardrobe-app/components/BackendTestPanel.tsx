'use client';

import { useState } from 'react';
import { APIClothingItem, ScoreRequest, ScoreResponse } from '@/types/api';

const API_BASE_URL = 'http://localhost:8000';

export default function BackendTestPanel() {
  const [isLoadingGet, setIsLoadingGet] = useState(false);
  const [isLoadingPost, setIsLoadingPost] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  /**
   * GET Button Handler
   * Fetches all items from backend and displays a random one
   */
  const handleGetRandomItem = async () => {
    setIsLoadingGet(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/items`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const items: APIClothingItem[] = await response.json();
      console.log('Full response from GET /items:', items);

      if (items.length === 0) {
        alert('No items found in the backend!');
        return;
      }

      // Randomly select one item
      const randomIndex = Math.floor(Math.random() * items.length);
      const randomItem = items[randomIndex];

      // Display selected item in alert
      // TODO: Replace with a modal component for better UX
      alert(
        `Random Item:\n\n` +
        `Name: ${randomItem.name || 'N/A'}\n` +
        `Category: ${randomItem.category}\n` +
        `Color: ${randomItem.color}\n` +
        `Formality: ${randomItem.formality}`
      );

    } catch (error) {
      console.error('Error fetching items:', error);
      setErrorMessage('Backend not connected. Make sure FastAPI is running on port 8000.');
      alert('Error: Backend not connected. Please start the FastAPI server.');
    } finally {
      setIsLoadingGet(false);
    }
  };

  /**
   * POST Button Handler
   * Sends item IDs to backend for compatibility scoring
   */
  const handleTestBackend = async () => {
    setIsLoadingPost(true);
    setErrorMessage(null);

    try {
      const payload: ScoreRequest = {
        item_ids: [1, 2, 3],
      };

      const response = await fetch(`${API_BASE_URL}/score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: ScoreResponse = await response.json();
      console.log('Full response from POST /score:', result);

      // Display the score in alert
      // TODO: Replace with a modal or notification component
      alert(
        `Outfit Compatibility Score:\n\n` +
        `Score: ${result.score}\n` +
        `Items: [${result.item_ids.join(', ')}]\n\n` +
        `Check your FastAPI terminal for the print statement!`
      );

    } catch (error) {
      console.error('Error scoring outfit:', error);
      setErrorMessage('Backend not connected. Make sure FastAPI is running on port 8000.');
      alert('Error: Backend not connected. Please start the FastAPI server.');
    } finally {
      setIsLoadingPost(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Backend Integration Test</h2>

      {/* Error Message Display */}
      {errorMessage && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-800">{errorMessage}</p>
          <p className="text-xs text-red-600 mt-1">
            Run: <code className="bg-red-100 px-2 py-1 rounded">uvicorn main:app --reload --port 8000</code>
          </p>
        </div>
      )}

      {/* Button Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* GET Button */}
        <button
          onClick={handleGetRandomItem}
          disabled={isLoadingGet}
          className={`
            flex-1 px-6 py-3 rounded-lg font-medium text-white
            transition-all duration-200
            ${isLoadingGet
              ? 'bg-blue-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg active:scale-95'
            }
          `}
        >
          {isLoadingGet ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          ) : (
            'Get Random Item'
          )}
        </button>

        {/* POST Button */}
        <button
          onClick={handleTestBackend}
          disabled={isLoadingPost}
          className={`
            flex-1 px-6 py-3 rounded-lg font-medium text-white
            transition-all duration-200
            ${isLoadingPost
              ? 'bg-green-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-700 hover:shadow-lg active:scale-95'
            }
          `}
        >
          {isLoadingPost ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          ) : (
            'Test Backend (Score)'
          )}
        </button>
      </div>

      {/* Info Text */}
      <div className="mt-4 text-sm text-gray-600">
        <p>
          <strong>Get Random Item:</strong> Fetches all items from <code className="bg-gray-100 px-2 py-1 rounded text-xs">GET /items</code> and displays one randomly
        </p>
        <p className="mt-2">
          <strong>Test Backend:</strong> Sends compatibility score request to <code className="bg-gray-100 px-2 py-1 rounded text-xs">POST /score</code>
        </p>
      </div>
    </div>
  );
}
