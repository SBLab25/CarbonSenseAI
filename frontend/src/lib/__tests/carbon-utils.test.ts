import { describe, test, expect } from 'vitest';
import { formatKg, getEcoTier, getCategoryColor } from '../utils';

describe('carbon-utils helper tests', () => {
  test('formatKg formats values correctly', () => {
    expect(formatKg(4.2)).toBe('4.2 kg CO₂');
    expect(formatKg(10.0)).toBe('10.0 kg CO₂');
  });

  test('formatKg handles float precision and rounding', () => {
    expect(formatKg(0.001)).toBe('0.0 kg CO₂');
    expect(formatKg(4.56)).toBe('4.6 kg CO₂');
  });

  test('getEcoTier evaluates points threshold tiers correctly', () => {
    expect(getEcoTier(0)).toBe('Seedling');
    expect(getEcoTier(199)).toBe('Seedling');
    expect(getEcoTier(200)).toBe('Sapling');
    expect(getEcoTier(499)).toBe('Sapling');
    expect(getEcoTier(500)).toBe('Tree');
    expect(getEcoTier(999)).toBe('Tree');
    expect(getEcoTier(1000)).toBe('Forest');
    expect(getEcoTier(2500)).toBe('Forest');
  });

  test('getCategoryColor returns correct hex styling', () => {
    expect(getCategoryColor('transport')).toBe('#2563eb');
    expect(getCategoryColor('energy')).toBe('#d97706');
    expect(getCategoryColor('food')).toBe('#16a34a');
    expect(getCategoryColor('shopping')).toBe('#9333ea');
    
    // Fallback case
    expect(getCategoryColor('unknown_category')).toBe('#6b7280');
  });
});
