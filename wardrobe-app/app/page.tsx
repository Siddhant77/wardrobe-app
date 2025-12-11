import Link from 'next/link';
import ImageUpload from '@/components/ImageUpload';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center max-w-2xl w-full">
        <h1 className="text-4xl font-bold mb-4">Wardrobe Manager</h1>
        <p className="text-lg text-gray-600 mb-8">
          Organize and manage your wardrobe collection
        </p>
        <div className="flex gap-6 justify-center mb-12">
          <Link
            href="/wardrobe"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Gallery
          </Link>
          <Link
            href="/outfit"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Recommend Outfit
          </Link>
        </div>

        <div className="border-t pt-12">
          <h2 className="text-2xl font-bold mb-6">Upload New Item</h2>
          <ImageUpload />
        </div>
      </div>
    </main>
  );
}
