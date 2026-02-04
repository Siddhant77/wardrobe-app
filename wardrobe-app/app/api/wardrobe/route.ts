import { NextRequest, NextResponse } from 'next/server';

// Use internal Docker network URL for server-side calls
const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://backend:8000';

export async function GET(request: NextRequest) {
  try {
    // Proxy request to FastAPI backend
    const response = await fetch(`${BACKEND_API_URL}/items`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error(`Backend API error: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { error: 'Failed to fetch items from backend' },
        { status: response.status }
      );
    }

    const items = await response.json();

    // Transform backend response to match frontend ClothingItem type
    const transformedItems = items.map((item: any) => ({
      id: item.id.toString(),
      filename: item.image_name,
      imagePath: item.image_url,
      category: item.category.toLowerCase(),
      weatherLabel: item.weather_label,
      formalityLabel: item.formality_label,
    }));

    return NextResponse.json(transformedItems, { status: 200 });
  } catch (error) {
    console.error('Error fetching items from backend:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
