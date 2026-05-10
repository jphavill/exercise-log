import { describe, expect, it, vi } from 'vitest';
import { firstValueFrom, of } from 'rxjs';

import { ApiService } from './api.service';

describe('ApiService', () => {
  it('requests exercises from the exercises endpoint', () => {
    const response = Symbol('response');
    const http = { get: vi.fn().mockReturnValue(response) } as any;
    const service = new ApiService(http);

    expect(service.getExercises()).toBe(response);
    expect(http.get).toHaveBeenCalledWith('/api/exercises');
  });

  it('posts create payload to exercises endpoint', () => {
    const response = Symbol('response');
    const http = { post: vi.fn().mockReturnValue(response) } as any;
    const service = new ApiService(http);
    const payload = {
      slug: 'bench-press',
      name: 'Bench Press',
      metric_type: 'reps' as const,
      sort_order: 1,
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    };

    expect(service.createExercise(payload)).toBe(response);
    expect(http.post).toHaveBeenCalledWith('/api/exercises', payload);
  });

  it('builds ids and query params for detail endpoints', () => {
    const response = Symbol('response');
    const http = {
      get: vi.fn().mockReturnValue(response),
      put: vi.fn().mockReturnValue(response),
      delete: vi.fn().mockReturnValue(response),
    } as any;
    const service = new ApiService(http);

    service.updateExercise(7, {
      name: 'Bench',
      metric_type: 'reps',
      sort_order: 2,
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    });
    service.deleteExercise(7);
    service.getExerciseHistory('bench-press', 45);
    service.getRecentLogs(10);

    expect(http.put).toHaveBeenCalledWith('/api/exercises/7', {
      name: 'Bench',
      metric_type: 'reps',
      sort_order: 2,
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    });
    expect(http.delete).toHaveBeenCalledWith('/api/exercises/7');
    expect(http.get).toHaveBeenCalledWith('/api/exercises/bench-press/history?days=45');
    expect(http.get).toHaveBeenCalledWith('/api/logs/recent?limit=10');
  });

  it('uses dashboard and reorder endpoints', () => {
    const response = Symbol('response');
    const http = {
      get: vi.fn().mockReturnValue(response),
      put: vi.fn().mockReturnValue(response),
    } as any;
    const service = new ApiService(http);
    const payload = { items: [{ id: 1, sort_order: 3 }] };

    expect(service.getDashboardSummary()).toBe(response);
    expect(service.reorderExercises(payload)).toBe(response);
    expect(http.get).toHaveBeenCalledWith('/api/dashboard/summary');
    expect(http.put).toHaveBeenCalledWith('/api/exercises/reorder', payload);
  });

  it('accepts workouts returned as an object or top-level array', async () => {
    const workout = {
      id: 1,
      name: ' Pull-up Ladder ',
      duration_min: 12,
      steps: [{ kind: 'rep_exercise', title: ' Pull-ups ', reps: 5, rep_unit: ' reps ' }],
    };
    const http = { get: vi.fn().mockReturnValueOnce(of({ workouts: [workout] })).mockReturnValueOnce(of([workout])) } as any;
    const service = new ApiService(http);

    await expect(firstValueFrom(service.getWorkouts())).resolves.toEqual([
      {
        id: 1,
        name: 'Pull-up Ladder',
        duration_min: 12,
        steps: [{ kind: 'rep_exercise', title: 'Pull-ups', reps: 5, rep_unit: 'reps' }],
      },
    ]);
    await expect(firstValueFrom(service.getWorkouts())).resolves.toHaveLength(1);
    expect(http.get).toHaveBeenCalledWith('/api/workouts');
  });

  it('fetches and validates a specific workout', async () => {
    const workout = {
      id: 4,
      name: ' Grip Circuit ',
      duration_min: 8,
      steps: [{ kind: 'timed_exercise', title: ' Dead hang ', duration_sec: 30 }],
    };
    const http = { get: vi.fn().mockReturnValue(of(workout)) } as any;
    const service = new ApiService(http);

    await expect(firstValueFrom(service.getWorkout(4))).resolves.toEqual({
      id: 4,
      name: 'Grip Circuit',
      duration_min: 8,
      steps: [{ kind: 'timed_exercise', title: 'Dead hang', duration_sec: 30 }],
    });
    expect(http.get).toHaveBeenCalledWith('/api/workouts/4');
  });

  it('rejects invalid workouts payloads', async () => {
    const http = { get: vi.fn().mockReturnValue(of({ workouts: [{ id: 1, name: '', duration_min: 12, steps: [] }] })) } as any;
    const service = new ApiService(http);

    await expect(firstValueFrom(service.getWorkouts())).rejects.toThrow('Invalid workouts payload');
  });

  it('fetches and validates workout definitions for editor mode', async () => {
    const workout = {
      id: 4,
      name: ' Grip Circuit ',
      duration_min: 8,
      enabled: false,
      sort_order: 3,
      updated_at: ' 2026-05-10T12:00:00Z ',
      definition: {
        steps: [{ kind: 'rest', title: ' Rest ', duration_sec: 45 }],
      },
    };
    const http = {
      get: vi.fn().mockReturnValueOnce(of({ workouts: [workout] })).mockReturnValueOnce(of(workout)),
    } as any;
    const service = new ApiService(http);

    await expect(firstValueFrom(service.getWorkoutDefinitions())).resolves.toEqual([
      {
        id: 4,
        name: 'Grip Circuit',
        duration_min: 8,
        enabled: false,
        sort_order: 3,
        updated_at: '2026-05-10T12:00:00Z',
        definition: { steps: [{ kind: 'rest', title: 'Rest', duration_sec: 45 }] },
      },
    ]);
    await expect(firstValueFrom(service.getWorkoutDefinition(4))).resolves.toEqual({
      id: 4,
      name: 'Grip Circuit',
      duration_min: 8,
      enabled: false,
      sort_order: 3,
      updated_at: '2026-05-10T12:00:00Z',
      definition: { steps: [{ kind: 'rest', title: 'Rest', duration_sec: 45 }] },
    });
    expect(http.get).toHaveBeenCalledWith('/api/workouts?include_disabled=true&detail=definition');
    expect(http.get).toHaveBeenCalledWith('/api/workouts/4?include_disabled=true&detail=definition');
  });

  it('uses workout editor write endpoints', async () => {
    const response = { id: 1 };
    const http = {
      post: vi.fn().mockReturnValue(response),
      put: vi.fn().mockReturnValueOnce(response).mockReturnValueOnce(of({ workouts: [] })),
      patch: vi.fn().mockReturnValue(response),
      delete: vi.fn().mockReturnValue(response),
    } as any;
    const service = new ApiService(http);
    const payload = {
      name: 'New Workout',
      enabled: false,
      sort_order: 1,
      definition: { steps: [{ kind: 'timed_exercise' as const, title: 'Hang', duration_sec: 30 }] },
    };

    expect(service.createWorkout(payload)).toBe(response);
    expect(service.updateWorkout(7, payload)).toBe(response);
    expect(service.updateWorkoutEnabled(7, { enabled: true })).toBe(response);
    await expect(firstValueFrom(service.reorderWorkouts({ items: [{ id: 7, sort_order: 2 }] }))).resolves.toEqual([]);
    expect(service.deleteWorkout(7)).toBe(response);

    expect(http.post).toHaveBeenCalledWith('/api/workouts', payload);
    expect(http.put).toHaveBeenCalledWith('/api/workouts/7', payload);
    expect(http.patch).toHaveBeenCalledWith('/api/workouts/7/enabled', { enabled: true });
    expect(http.put).toHaveBeenCalledWith('/api/workouts/reorder', { items: [{ id: 7, sort_order: 2 }] });
    expect(http.delete).toHaveBeenCalledWith('/api/workouts/7');
  });

  it('rejects invalid workout definition payloads', async () => {
    const http = {
      get: vi.fn().mockReturnValue(of({ workouts: [{ id: 1, name: 'Workout', duration_min: 1, enabled: true, sort_order: 1, updated_at: 'now', definition: { steps: [] } }] })),
    } as any;
    const service = new ApiService(http);

    await expect(firstValueFrom(service.getWorkoutDefinitions())).rejects.toThrow('Invalid workouts payload');
  });
});
