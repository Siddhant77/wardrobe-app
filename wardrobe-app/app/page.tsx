import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Wardrobe Manager</h1>
        <p className="text-lg text-gray-600 mb-8">
          Organize and manage your wardrobe collection
        </p>
        <div className="flex gap-6 justify-center">
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
      </div>
    </main>
  );
}
