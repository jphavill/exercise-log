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
    expect(component.openMenuLogId).toBeNull();
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
