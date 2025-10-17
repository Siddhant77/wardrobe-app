import { promises as fs } from 'fs';
import path from 'path';
import GalleryGrid from '@/components/GalleryGrid';
import BackendTestPanel from '@/components/BackendTestPanel';
import { ClothingItem } from '@/types/clothing';

async function getWardrobeItems(): Promise<ClothingItem[]> {
  const wardrobeDir = path.join(process.cwd(), 'public', 'wardrobe');

  try {
    // Check if wardrobe directory exists
    await fs.access(wardrobeDir);
    const files = await fs.readdir(wardrobeDir);

    // Filter for image files
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    const imageFiles = files.filter((file) => {
      const ext = path.extname(file).toLowerCase();
      return imageExtensions.includes(ext);
    });

    // Map to ClothingItem objects
    const items: ClothingItem[] = imageFiles.map((file) => ({
      id: file, // Use filename as ID for now
      filename: file,
      imagePath: `/wardrobe/${file}`,
      // TODO: When API integration is added, fetch metadata from database here
      // Example: category, color, formality, season, etc.
    }));

    return items;
  } catch (error) {
    // Directory doesn't exist or is empty
    console.warn('Wardrobe directory not found or empty:', error);
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
        {/* Backend Integration Test Panel */}
        <BackendTestPanel />

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
