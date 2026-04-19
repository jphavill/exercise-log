import { describe, expect, it } from 'vitest';

import { TrendLineService } from './trend-line.service';

describe('TrendLineService', () => {
  const service = new TrendLineService();

  it('builds a single linear trend for gradual data', () => {
    const data = [2, 4, 5, 7, 9, 10, 11, 13, 15, 16, 18, 19, 21, 22];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndex).toBeNull();
    expect(result.breakIndices).toEqual([]);
    expect(result.segments).toHaveLength(1);
    expect(result.values).toHaveLength(data.length);
    expect(result.values[0]).toBeLessThan(result.values[result.values.length - 1]);
  });

  it('splits into piecewise trends when there is a large shift', () => {
    const data = [2, 3, 4, 5, 6, 7, 8, 26, 27, 28, 29, 30, 31, 32];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndices.length).toBeGreaterThan(0);
    expect(result.breakIndex).toBe(result.breakIndices[0]);
    expect(result.values).toHaveLength(data.length);
    const firstBreak = result.breakIndices[0];
    expect(firstBreak).toBeGreaterThan(0);
    const jump = Math.abs(result.values[firstBreak] - result.values[firstBreak - 1]);
    expect(jump).toBeGreaterThan(10);
  });

  it('supports missed days in trend calculations', () => {
    const data = [0, 0, 2, 0, 4, 0, 6, 0, 8, 0, 10, 0, 12, 0, 14, 0, 16, 0, 18, 0, 20, 0, 22, 0, 24, 0, 26, 0, 28, 0];

    const result = service.buildSegmentedTrend(data);

    expect(result.values).toHaveLength(data.length);
    expect(result.values[0]).toBeLessThan(result.values[result.values.length - 1]);
  });

  it('returns original shape for very short input', () => {
    const data = [10];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndex).toBeNull();
    expect(result.breakIndices).toEqual([]);
    expect(result.values).toEqual([10]);
  });

  it('does not split constant data', () => {
    const data = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndex).toBeNull();
    expect(result.breakIndices).toEqual([]);
    expect(result.values.every((value) => Math.abs(value - 5) < 0.0001)).toBe(true);
  });

  it('does not over-segment mild noise', () => {
    const data = [10, 11, 9, 12, 11, 10, 12, 13, 12, 11, 13, 12, 14, 13, 12, 14, 13, 12];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndex).toBeNull();
    expect(result.breakIndices).toEqual([]);
    expect(result.values).toHaveLength(data.length);
  });

  it('does not split for a one-day spike with persistence of two', () => {
    const data = [10, 10, 10, 10, 40, 10, 10, 10, 10, 10, 10, 10];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndex).toBeNull();
    expect(result.breakIndices).toEqual([]);
  });

  it('splits for a sustained two-point shift', () => {
    const data = [8, 9, 10, 11, 28, 30, 31, 32, 33, 34, 35, 36];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndices.length).toBeGreaterThan(0);
    const firstBreak = result.breakIndices[0];
    expect(firstBreak).toBeGreaterThanOrEqual(4);
  });

  it('handles low baseline values using minimum percent base', () => {
    const data = [0, 0, 0, 1, 0, 0, 2, 0, 0, 1, 0, 0, 1, 0, 0];

    const result = service.buildSegmentedTrend(data);

    expect(result.values).toHaveLength(data.length);
    expect(result.breakIndices).toEqual([]);
  });

  it('supports multi-phase data with multiple breaks', () => {
    const data = [
      2, 3, 4, 5, 6, 7,
      24, 25, 26, 27, 28, 29,
      6, 7, 8, 9, 10, 11,
    ];

    const result = service.buildSegmentedTrend(data);

    expect(result.breakIndices.length).toBeGreaterThanOrEqual(2);
    expect(result.segments.length).toBe(result.breakIndices.length + 1);
    expect(result.breakIndex).toBe(result.breakIndices[0]);
  });
});
