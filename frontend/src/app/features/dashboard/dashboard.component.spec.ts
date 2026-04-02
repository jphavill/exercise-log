import { describe, expect, it, vi } from 'vitest';
import { of } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { DashboardSummary, ExerciseLog } from '../../models/api.models';

describe('DashboardComponent', () => {
  it('loads summary and recent logs on init', () => {
    const summary: DashboardSummary = {
      today: [],
      current_week: [],
      last_30_days: [],
      total_logs_today: 0,
      total_logs_this_week: 0,
    };
    const logs: ExerciseLog[] = [
      {
        id: 1,
        exercise_slug: 'push-ups',
        exercise_name: 'Push-ups',
        metric_type: 'reps',
        reps: 20,
        duration_seconds: null,
        weight_lbs: null,
        notes: null,
        logged_at: '2026-01-01T12:00:00Z',
      },
    ];
    const api = {
      getDashboardSummary: vi.fn().mockReturnValue(of(summary)),
      getRecentLogs: vi.fn().mockReturnValue(of(logs)),
    } as any;
    const component = new DashboardComponent(api);

    component.ngOnInit();

    expect(api.getDashboardSummary).toHaveBeenCalledOnce();
    expect(api.getRecentLogs).toHaveBeenCalledWith(20);
    expect(component.summary).toBe(summary);
    expect(component.recent).toEqual(logs);
  });

  it('formats recent metrics from metric type', () => {
    const component = new DashboardComponent({} as any);

    expect(
      component.formatRecent({
        id: 1,
        exercise_slug: 'bench-press',
        exercise_name: 'Bench Press',
        metric_type: 'reps_plus_weight_lbs',
        reps: 5,
        duration_seconds: null,
        weight_lbs: 135,
        notes: null,
        logged_at: '2026-01-01T12:00:00Z',
      }),
    ).toBe('5 reps @ 135 lbs');

    expect(
      component.formatRecent({
        id: 2,
        exercise_slug: 'plank',
        exercise_name: 'Plank',
        metric_type: 'duration_seconds',
        reps: null,
        duration_seconds: 60,
        weight_lbs: null,
        notes: null,
        logged_at: '2026-01-01T12:00:00Z',
      }),
    ).toBe('60 sec');
  });

  it('clamps trend bars between 5 and 100', () => {
    const component = new DashboardComponent({} as any);

    expect(component.barPercent({ metric_type: 'reps', totals: { reps: 0, duration_seconds: null } })).toBe(5);
    expect(component.barPercent({ metric_type: 'reps', totals: { reps: 10, duration_seconds: null } })).toBe(40);
    expect(component.barPercent({ metric_type: 'duration_seconds', totals: { reps: null, duration_seconds: 50 } })).toBe(100);
  });
});
