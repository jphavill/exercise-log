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
      last_30_days_consistency: [],
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

  it('toggles row menu open and closed', () => {
    const component = new DashboardComponent({} as any);

    component.toggleMenu(12);
    expect(component.openMenuLogId).toBe(12);

    component.toggleMenu(12);
    expect(component.openMenuLogId).toBeNull();
  });

  it('removes a log after successful delete', () => {
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
      {
        id: 2,
        exercise_slug: 'squats',
        exercise_name: 'Squats',
        metric_type: 'reps',
        reps: 15,
        duration_seconds: null,
        weight_lbs: null,
        notes: null,
        logged_at: '2026-01-01T12:00:00Z',
      },
    ];
    const api = {
      deleteLog: vi.fn().mockReturnValue(of(undefined)),
    } as any;
    const component = new DashboardComponent(api);
    component.recent = logs;
    component.openMenuLogId = 2;

    component.deleteLog(2);

    expect(api.deleteLog).toHaveBeenCalledWith(2);
    expect(component.openMenuLogId).toBeNull();
    expect(component.recent.map((log) => log.id)).toEqual([1]);
  });
});
