import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatKg(kg: number): string {
  // If it's very small, display 0.0 or handle safely
  const val = kg || 0;
  return `${val.toFixed(1)} kg CO₂`;
}

export function formatPct(pct: number): string {
  const val = pct || 0;
  return `${val >= 0 ? '+' : ''}${val.toFixed(1)}%`;
}

export function getEcoTier(points: number): string {
  const pts = points || 0;
  if (pts >= 1000) return 'Forest';
  if (pts >= 500) return 'Tree';
  if (pts >= 200) return 'Sapling';
  return 'Seedling';
}

export function getCategoryColor(category: string): string {
  const cat = (category || '').toLowerCase().trim();
  if (cat === 'transport') return '#2563eb';
  if (cat === 'energy') return '#d97706';
  if (cat === 'food') return '#16a34a';
  if (cat === 'shopping') return '#9333ea';
  return '#6b7280'; // gray-500 fallback
}
