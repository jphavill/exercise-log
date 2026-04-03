import { describe, expect, it, vi } from 'vitest';
import { of } from 'rxjs';

import { ExerciseDetailComponent } from './exercise-detail.component';
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
    const component = new ExerciseDetailComponent(api, route);

    component.ngOnInit();

    expect(api.getExerciseHistory).toHaveBeenCalledWith('plank', 30);
    expect(component.history).toBe(history);
  });

  it('formats totals using current exercise metric type', () => {
    const component = new ExerciseDetailComponent({} as any, {} as any);

    expect(component.formatTotals({ reps: 7, duration_seconds: null })).toBe('0');

    component.history = createHistory('duration_seconds');
    expect(component.formatTotals({ reps: 7, duration_seconds: 45 })).toBe('45 sec');
  });

  it('toggles smoothed trend option', () => {
    const component = new ExerciseDetailComponent({} as any, {} as any);
    component.history = createHistory('reps');

    component.toggleSmoothedTrend();

    expect(component.showSmoothedTrend).toBe(true);
  });

  it('formats logs from explicit metric type', () => {
    const component = new ExerciseDetailComponent({} as any, {} as any);

    expect(component.formatLog({ metric_type: 'reps', reps: 9, duration_seconds: null, weight_lbs: null } as any)).toBe('9 reps');
    expect(component.formatLog({ metric_type: 'duration_seconds', reps: 9, duration_seconds: 75, weight_lbs: null } as any)).toBe('75 sec');
  });
});
