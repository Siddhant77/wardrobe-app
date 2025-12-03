import { promises as fs } from 'fs';
import path from 'path';
import GalleryGrid from '@/components/GalleryGrid';
import { ClothingItem } from '@/types/clothing';

async function getWardrobeItems(): Promise<ClothingItem[]> {
  const metadataPath = path.join(process.cwd(), 'public', 'metadata.csv');

  try {
    // Read metadata.csv
    const csvContent = await fs.readFile(metadataPath, 'utf-8');
    const lines = csvContent.trim().split('\n');

    if (lines.length < 2) {
      console.warn('Metadata.csv is empty or missing headers');
      return [];
    }

    // Parse CSV header
    const headers = lines[0].split(',');
    const idIndex = headers.indexOf('id');
    const imageNameIndex = headers.indexOf('image_name');
    const imagePathIndex = headers.indexOf('image_path');
    const categoryIndex = headers.indexOf('item_category');
    const weatherLabelIndex = headers.indexOf('weather_label');
    const formalityLabelIndex = headers.indexOf('formality_label');

    if (idIndex === -1 || imagePathIndex === -1) {
      console.warn('Required columns (id, image_path) not found in metadata.csv');
      return [];
    }

    // Parse CSV data rows
    const items: ClothingItem[] = lines.slice(1).map((line) => {
      const values = line.split(',');
      return {
        id: values[idIndex]?.trim() || '',
        filename: values[imageNameIndex]?.trim() || '',
        imagePath: `/wardrobe/${values[imagePathIndex]?.trim() || ''}`,
        category: values[categoryIndex]?.trim() || 'Unknown',
        weatherLabel: weatherLabelIndex !== -1 ? parseInt(values[weatherLabelIndex]?.trim() || '0', 10) : undefined,
        formalityLabel: formalityLabelIndex !== -1 ? parseInt(values[formalityLabelIndex]?.trim() || '0', 10) : undefined,
      };
    });

    return items;
  } catch (error) {
    // Metadata.csv doesn't exist or can't be read
    console.warn('Could not read metadata.csv:', error);
    return [];
  }
}

export default async function WardrobePage() {
  // TODO: Replace with API call when backend is ready
  // const items = await fetch('/api/wardrobe').then(res => res.json());
  const items = await getWardrobeItems();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">My Wardrobe</h1>
          <p className="mt-2 text-sm text-gray-600">
            {items.length} {items.length === 1 ? 'item' : 'items'} in your collection
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* TODO: Add filter/search bar here when implementing filtering functionality */}
        {/* <div className="mb-6">
          <WardrobeFilters />
        </div> */}

        <GalleryGrid items={items} />
      </main>
    </div>
  );
}

// Enable dynamic rendering to read from filesystem
export const dynamic = 'force-dynamic';
