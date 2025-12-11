import { promises as fs } from 'fs';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { ClothingItem } from '@/types/clothing';

export async function GET(request: NextRequest) {
  const metadataPath = path.join(process.cwd(), 'public', 'metadata.csv');

  try {
    // Read metadata.csv
    const csvContent = await fs.readFile(metadataPath, 'utf-8');
    const lines = csvContent.trim().split('\n');

    if (lines.length < 2) {
      return NextResponse.json([], { status: 200 });
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
      return NextResponse.json([], { status: 200 });
    }

    // Parse CSV data rows
    const items: ClothingItem[] = lines.slice(1).map((line) => {
      const values = line.split(',');
      return {
        id: values[idIndex]?.trim() || '',
        filename: values[imageNameIndex]?.trim() || '',
        imagePath: `/wardrobe/${values[imagePathIndex]?.trim() || ''}`,
        category: (values[categoryIndex]?.trim() || 'Unknown').toLowerCase() as any,
        weatherLabel: weatherLabelIndex !== -1 ? parseInt(values[weatherLabelIndex]?.trim() || '0', 10) : undefined,
        formalityLabel: formalityLabelIndex !== -1 ? parseInt(values[formalityLabelIndex]?.trim() || '0', 10) : undefined,
      };
    });

    return NextResponse.json(items, { status: 200 });
  } catch (error) {
    console.error('Error reading wardrobe metadata:', error);
    return NextResponse.json([], { status: 200 });
  }
}
