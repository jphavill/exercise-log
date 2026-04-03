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

  it('returns top 6 consistency rows sorted by activity', () => {
    const component = new DashboardComponent({} as any);
    component.summary = {
      today: [],
      current_week: [],
      last_30_days: [],
      total_logs_today: 0,
      total_logs_this_week: 0,
      last_30_days_consistency: [
        {
          exercise_id: 1,
          exercise_slug: 'pullups',
          exercise_name: 'Pullups',
          metric_type: 'reps',
          window_totals: { reps: 50, duration_seconds: null },
          active_days: 5,
          total_logs: 7,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
        {
          exercise_id: 2,
          exercise_slug: 'plank',
          exercise_name: 'Plank',
          metric_type: 'duration_seconds',
          window_totals: { reps: null, duration_seconds: 300 },
          active_days: 8,
          total_logs: 8,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
        {
          exercise_id: 3,
          exercise_slug: 'squats',
          exercise_name: 'Squats',
          metric_type: 'reps',
          window_totals: { reps: 100, duration_seconds: null },
          active_days: 8,
          total_logs: 6,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
        {
          exercise_id: 4,
          exercise_slug: 'burpees',
          exercise_name: 'Burpees',
          metric_type: 'reps',
          window_totals: { reps: 20, duration_seconds: null },
          active_days: 2,
          total_logs: 2,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
        {
          exercise_id: 5,
          exercise_slug: 'situps',
          exercise_name: 'Situps',
          metric_type: 'reps',
          window_totals: { reps: 25, duration_seconds: null },
          active_days: 4,
          total_logs: 4,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
        {
          exercise_id: 6,
          exercise_slug: 'dips',
          exercise_name: 'Dips',
          metric_type: 'reps',
          window_totals: { reps: 33, duration_seconds: null },
          active_days: 3,
          total_logs: 5,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
        {
          exercise_id: 7,
          exercise_slug: 'rows',
          exercise_name: 'Rows',
          metric_type: 'reps',
          window_totals: { reps: 15, duration_seconds: null },
          active_days: 1,
          total_logs: 1,
          scaling_mode: 'relative',
          goal_target_value: null,
          goal_weight_lbs: null,
          days: [],
        },
      ],
    };

    const rows = component.topConsistencyRows();

    expect(rows).toHaveLength(6);
    expect(rows.map((row) => row.exercise_slug)).toEqual(['plank', 'squats', 'pullups', 'situps', 'dips', 'burpees']);
  });

  it('maps heat cell class from API intensity level', () => {
    const component = new DashboardComponent({} as any);
    const row = {
      exercise_id: 1,
      exercise_slug: 'pullups',
      exercise_name: 'Pullups',
      metric_type: 'reps' as const,
      window_totals: { reps: 17, duration_seconds: null },
      active_days: 4,
      total_logs: 4,
      scaling_mode: 'goal' as const,
      goal_target_value: 8,
      goal_weight_lbs: null,
      days: [
        { day: '2026-01-01', totals: { reps: 0, duration_seconds: null }, progress_value: 0, intensity_level: 0 as const },
        { day: '2026-01-02', totals: { reps: 1, duration_seconds: null }, progress_value: 1, intensity_level: 1 as const },
        { day: '2026-01-03', totals: { reps: 3, duration_seconds: null }, progress_value: 3, intensity_level: 2 as const },
        { day: '2026-01-04', totals: { reps: 5, duration_seconds: null }, progress_value: 5, intensity_level: 3 as const },
        { day: '2026-01-05', totals: { reps: 8, duration_seconds: null }, progress_value: 8, intensity_level: 4 as const },
      ],
    };

    expect(component.heatLevelClass(row, row.days[0])).toBe('level-0');
    expect(component.heatLevelClass(row, row.days[1])).toBe('level-1');
    expect(component.heatLevelClass(row, row.days[2])).toBe('level-2');
    expect(component.heatLevelClass(row, row.days[3])).toBe('level-3');
    expect(component.heatLevelClass(row, row.days[4])).toBe('level-4');
    expect(component.heatCellTitle(row, row.days[4])).toContain('8 reps');
  });
});
