import { describe, expect, it, vi } from 'vitest';
import { of } from 'rxjs';

import { ExerciseDetailComponent } from './exercise-detail.component';
import { TrendLineService } from './trend-line.service';
import { ExerciseHistory } from '../../models/api.models';

function createHistory(metricType: 'duration_seconds' | 'reps' = 'reps'): ExerciseHistory {
  return {
    exercise: {
      id: 1,
      slug: 'plank',
      name: 'Plank',
      metric_type: metricType,
      sort_order: 1,
      goal_reps: metricType === 'duration_seconds' ? null : 40,
      goal_duration_seconds: metricType === 'duration_seconds' ? 40 : null,
      goal_weight_lbs: null,
    },
    days: [{ day: '2026-03-31', totals: { reps: 5, duration_seconds: 60 }, goal_progress_value: 5 }],
    current_streak: 3,
    best_day: { day: '2026-03-30', totals: { reps: 10, duration_seconds: 120 } },
    all_time_total: { reps: 50, duration_seconds: 600 },
    today_total: { reps: 2, duration_seconds: 30 },
    last_7_days_total: { reps: 20, duration_seconds: 240 },
    last_30_days_total: { reps: 40, duration_seconds: 480 },
    recent_logs: [],
  };
}

describe('ExerciseDetailComponent', () => {
  const trendLineService = new TrendLineService();

  it('loads history from route slug on init', () => {
    const history = createHistory();
    const api = {
      getExerciseHistory: vi.fn().mockReturnValue(of(history)),
    } as any;
    const route = {
      snapshot: {
        paramMap: {
          get: vi.fn().mockReturnValue('plank'),
        },
      },
    } as any;
    const component = new ExerciseDetailComponent(api, route, trendLineService);

    component.ngOnInit();

    expect(api.getExerciseHistory).toHaveBeenCalledWith('plank', 30);
    expect(component.history).toBe(history);
  });

  it('formats totals using current exercise metric type', () => {
    const component = new ExerciseDetailComponent({} as any, {} as any, trendLineService);

    expect(component.formatTotals({ reps: 7, duration_seconds: null })).toBe('0');

    component.history = createHistory('duration_seconds');
    expect(component.formatTotals({ reps: 7, duration_seconds: 45 })).toBe('45 sec');
  });

  it('toggles trend line option', () => {
    const component = new ExerciseDetailComponent({} as any, {} as any, trendLineService);
    component.history = createHistory('reps');

    component.toggleTrendLine();

    expect(component.showTrendLine).toBe(true);
  });

  it('removes a log after successful delete', () => {
    const api = {
      deleteLog: vi.fn().mockReturnValue(of(undefined)),
    } as any;
    const component = new ExerciseDetailComponent(api, {} as any, trendLineService);
    component.history = {
      ...createHistory('reps'),
      recent_logs: [
        {
          id: 10,
          exercise_slug: 'plank',
          exercise_name: 'Plank',
          metric_type: 'reps',
          reps: 12,
          duration_seconds: null,
          weight_lbs: null,
          notes: null,
          logged_at: '2026-01-01T12:00:00Z',
        },
        {
          id: 11,
          exercise_slug: 'plank',
          exercise_name: 'Plank',
          metric_type: 'reps',
          reps: 8,
          duration_seconds: null,
          weight_lbs: null,
          notes: null,
          logged_at: '2026-01-01T12:10:00Z',
        },
      ],
    };
    component.openMenuLogId = 11;

    component.deleteLog(11);

    expect(api.deleteLog).toHaveBeenCalledWith(11);
    expect(component.openMenuLogId).toBeNull();
    expect(component.history?.recent_logs.map((log) => log.id)).toEqual([10]);
  });
});
