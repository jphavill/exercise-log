import { describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { ExerciseLog } from '../../../../models/api.models';
import { RecentActivitySectionComponent } from './recent-activity-section.component';

function createLog(overrides: Partial<ExerciseLog> = {}): ExerciseLog {
  return {
    id: 1,
    exercise_slug: 'plank',
    exercise_name: 'Plank',
    metric_type: 'reps',
    reps: 12,
    duration_seconds: null,
    weight_lbs: null,
    notes: null,
    logged_at: '2026-01-01T12:00:00Z',
    ...overrides,
  };
}

const templatePath = resolve(dirname(fileURLToPath(import.meta.url)), './recent-activity-section.component.html');

describe('RecentActivitySectionComponent', () => {
  it('starts with empty defaults', () => {
    const component = new RecentActivitySectionComponent();

    expect(component.recent).toEqual([]);
    expect(component.visibleRecent).toEqual([]);
    expect(component.openMenuLogId).toBeNull();
  });

  it('shows only 10 logs initially when more are provided', () => {
    const component = new RecentActivitySectionComponent();
    const logs = Array.from({ length: 15 }, (_, index) => createLog({ id: index + 1 }));

    component.recent = logs;

    expect(component.visibleRecent).toHaveLength(10);
    expect(component.hasMore).toBe(true);
    expect(component.nextBatchCount).toBe(5);
    expect(component.controls).toEqual({ showMore: true, showLess: false, nextBatchCount: 5 });
  });

  it('shows more logs in batches of 10 and supports collapse before fully expanded', () => {
    const component = new RecentActivitySectionComponent();
    const logs = Array.from({ length: 25 }, (_, index) => createLog({ id: index + 1 }));
    component.recent = logs;

    component.showMore();
    expect(component.visibleRecent).toHaveLength(20);
    expect(component.hasMore).toBe(true);
    expect(component.canCollapse).toBe(true);
    expect(component.controls).toEqual({ showMore: true, showLess: true, nextBatchCount: 5 });

    component.showLess();
    expect(component.visibleRecent).toHaveLength(10);
    expect(component.hasMore).toBe(true);

    component.showMore();
    component.showMore();
    expect(component.visibleRecent).toHaveLength(25);
    expect(component.hasMore).toBe(false);
    expect(component.controls).toEqual({ showMore: false, showLess: true, nextBatchCount: 0 });

    component.showLess();
    expect(component.visibleRecent).toHaveLength(10);
    expect(component.hasMore).toBe(true);
  });

  it('preserves expanded state when incoming recent data grows', () => {
    const component = new RecentActivitySectionComponent();
    component.recent = Array.from({ length: 25 }, (_, index) => createLog({ id: index + 1 }));

    component.showMore();
    expect(component.visibleRecent).toHaveLength(20);

    component.recent = Array.from({ length: 30 }, (_, index) => createLog({ id: index + 1 }));
    expect(component.visibleRecent).toHaveLength(20);
    expect(component.hasMore).toBe(true);
    expect(component.nextBatchCount).toBe(10);
  });

  it('clamps visible logs when incoming recent data shrinks', () => {
    const component = new RecentActivitySectionComponent();
    component.recent = Array.from({ length: 25 }, (_, index) => createLog({ id: index + 1 }));

    component.showMore();
    expect(component.visibleRecent).toHaveLength(20);

    component.recent = Array.from({ length: 12 }, (_, index) => createLog({ id: index + 1 }));
    expect(component.visibleRecent).toHaveLength(12);
    expect(component.hasMore).toBe(false);
    expect(component.canCollapse).toBe(true);
  });

  it('reinitializes visible count after empty to non-empty transition', () => {
    const component = new RecentActivitySectionComponent();
    component.recent = Array.from({ length: 15 }, (_, index) => createLog({ id: index + 1 }));

    component.showMore();
    expect(component.visibleRecent).toHaveLength(15);

    component.recent = [];
    expect(component.visibleRecent).toHaveLength(0);

    component.recent = Array.from({ length: 8 }, (_, index) => createLog({ id: index + 1 }));
    expect(component.visibleRecent).toHaveLength(8);
    expect(component.hasMore).toBe(false);
  });

  it.each([
    { total: 0, expectedVisible: 0, expectedHasMore: false, expectedNextBatch: 0 },
    { total: 1, expectedVisible: 1, expectedHasMore: false, expectedNextBatch: 0 },
    { total: 10, expectedVisible: 10, expectedHasMore: false, expectedNextBatch: 0 },
    { total: 11, expectedVisible: 10, expectedHasMore: true, expectedNextBatch: 1 },
    { total: 20, expectedVisible: 10, expectedHasMore: true, expectedNextBatch: 10 },
  ])(
    'handles boundary count $total on first load',
    ({ total, expectedVisible, expectedHasMore, expectedNextBatch }) => {
      const component = new RecentActivitySectionComponent();
      component.recent = Array.from({ length: total }, (_, index) => createLog({ id: index + 1 }));

      expect(component.visibleRecent).toHaveLength(expectedVisible);
      expect(component.hasMore).toBe(expectedHasMore);
      expect(component.nextBatchCount).toBe(expectedNextBatch);
    },
  );

  it('tracks logs by id', () => {
    const component = new RecentActivitySectionComponent();
    const log = createLog({ id: 42 });

    expect(component.trackByLogId(0, log)).toBe(42);
  });

  it('keeps a shared non-configurable heading', () => {
    const template = readFileSync(templatePath, 'utf8');

    expect(template).toContain('Recent Activity');
  });

  it('renders timestamps with date short format', () => {
    const template = readFileSync(templatePath, 'utf8');

    expect(template).toContain("date: 'short'");
  });

  it('formats reps metric', () => {
    const component = new RecentActivitySectionComponent();

    expect(component.formatRecent(createLog({ metric_type: 'reps', reps: 9 }))).toBe('9 reps');
  });

  it('formats duration metric', () => {
    const component = new RecentActivitySectionComponent();

    expect(component.formatRecent(createLog({ metric_type: 'duration_seconds', duration_seconds: 75 }))).toBe('75 sec');
  });

  it('formats weighted metric', () => {
    const component = new RecentActivitySectionComponent();

    expect(component.formatRecent(createLog({ metric_type: 'reps_plus_weight_lbs', reps: 5, weight_lbs: 135 }))).toBe('5 reps @ 135 lbs');
  });

  it('stops propagation and emits toggle event', () => {
    const component = new RecentActivitySectionComponent();
    const stopPropagation = vi.fn();
    const emitSpy = vi.spyOn(component.toggleMenuLog, 'emit');

    component.onToggleClick(42, { stopPropagation } as unknown as MouseEvent);

    expect(stopPropagation).toHaveBeenCalledOnce();
    expect(emitSpy).toHaveBeenCalledWith(42);
  });

  it('stops propagation when menu container is clicked', () => {
    const component = new RecentActivitySectionComponent();
    const stopPropagation = vi.fn();

    component.onMenuClick({ stopPropagation } as unknown as MouseEvent);

    expect(stopPropagation).toHaveBeenCalledOnce();
  });

  it('stops propagation and emits delete event', () => {
    const component = new RecentActivitySectionComponent();
    const stopPropagation = vi.fn();
    const emitSpy = vi.spyOn(component.deleteLogClick, 'emit');

    component.onDeleteClick(7, { stopPropagation } as unknown as MouseEvent);

    expect(stopPropagation).toHaveBeenCalledOnce();
    expect(emitSpy).toHaveBeenCalledWith(7);
  });
});
