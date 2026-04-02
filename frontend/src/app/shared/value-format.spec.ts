import { describe, expect, it } from 'vitest';

import { formatMetric } from './value-format';

describe('formatMetric', () => {
  it('formats duration metrics', () => {
    expect(formatMetric('duration_seconds', 5, 90)).toBe('90 sec');
    expect(formatMetric('duration_seconds', 5, null)).toBe('0 sec');
  });

  it('formats reps plus weight when both are present', () => {
    expect(formatMetric('reps_plus_weight_lbs', 8, null, 135)).toBe('8 reps @ 135 lbs');
  });

  it('falls back to reps when weight is missing', () => {
    expect(formatMetric('reps_plus_weight_lbs', 10, null, null)).toBe('10 reps');
    expect(formatMetric('reps_plus_weight_lbs', null, null, 185)).toBe('0 reps');
  });

  it('formats plain reps', () => {
    expect(formatMetric('reps', 12, null)).toBe('12 reps');
    expect(formatMetric('reps', null, null)).toBe('0 reps');
  });
});
