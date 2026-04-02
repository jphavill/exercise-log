import { describe, expect, it, vi } from 'vitest';

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
    const payload = { slug: 'bench-press', name: 'Bench Press', metric_type: 'reps', sort_order: 1 };

    expect(service.createExercise(payload)).toBe(response);
    expect(http.post).toHaveBeenCalledWith('/api/exercises', payload);
  });

  it('builds ids and query params for detail endpoints', () => {
    const response = Symbol('response');
    const http = {
      get: vi.fn().mockReturnValue(response),
      put: vi.fn().mockReturnValue(response),
    } as any;
    const service = new ApiService(http);

    service.updateExercise(7, { name: 'Bench', metric_type: 'reps', sort_order: 2 });
    service.getExerciseHistory('bench-press', 45);
    service.getRecentLogs(10);

    expect(http.put).toHaveBeenCalledWith('/api/exercises/7', { name: 'Bench', metric_type: 'reps', sort_order: 2 });
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
});
