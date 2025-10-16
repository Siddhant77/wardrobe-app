# Wardrobe Management System

A responsive image gallery built with Next.js 14+, TypeScript, and Tailwind CSS for managing your wardrobe collection.

## Features

- ✨ Responsive grid layout (2 columns mobile, 3-4 columns desktop)
- 🖼️ Optimized image loading with Next.js Image component
- 🔍 Full-size modal view with click interaction
- 🎨 Smooth hover effects with zoom and shadow transitions
- 📱 Mobile-friendly design
- 🚀 Future-ready with metadata placeholders for categories, colors, and formality

## Project Structure

```
wardrobe-app/
├── app/
│   └── wardrobe/
│       └── page.tsx          # Main gallery page
├── components/
│   ├── GalleryGrid.tsx       # Grid layout component
│   ├── ImageCard.tsx         # Individual image card
│   └── ImageModal.tsx        # Full-size image modal
├── types/
│   └── clothing.ts           # TypeScript interfaces
├── public/
│   └── wardrobe/             # Place your wardrobe images here
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Navigate to the project directory:
```bash
cd wardrobe-app
```

2. Install dependencies:
```bash
npm install
```

3. Add your wardrobe images:
   - Place your images in `/public/wardrobe/` folder
   - Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000/wardrobe](http://localhost:3000/wardrobe) in your browser

## Usage

### Adding Images

Simply drop your clothing images into the `public/wardrobe/` folder. The gallery will automatically detect and display them.

### Future Development

The app is designed to be extensible. Here are planned features:

#### API Integration
Currently, images are read directly from the filesystem. To integrate with an API:

1. Update `app/wardrobe/page.tsx` (line 29):
```typescript
// Replace filesystem read with API call
const items = await fetch('/api/wardrobe').then(res => res.json());
```

2. Create an API route at `app/api/wardrobe/route.ts` to serve clothing data

#### Metadata Support
The `ClothingItem` interface includes placeholders for:
- `category`: tops, bottoms, dresses, outerwear, shoes, accessories
- `color`: Array of color tags
- `formality`: casual, business-casual, formal, athletic
- `season`: spring, summer, fall, winter, all-season
- `brand`, `dateAdded`, `lastWorn`, `tags`

#### Filtering & Search
Add a filter component in `app/wardrobe/page.tsx` (line 50) to enable:
- Search by filename
- Filter by category, color, formality
- Sort by date added or last worn

## Technologies Used

- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first styling
- **Next.js Image** - Optimized image loading and lazy loading

## Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

## License

MIT
