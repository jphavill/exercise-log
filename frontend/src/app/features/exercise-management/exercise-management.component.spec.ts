import { describe, expect, it, vi } from 'vitest';
import { of, throwError } from 'rxjs';

import { ExerciseManagementComponent } from './exercise-management.component';
import { Exercise } from '../../models/api.models';

describe('ExerciseManagementComponent', () => {
  it('loads exercises during refresh', () => {
    const exercises: Exercise[] = [
      { id: 1, slug: 'pull-ups', name: 'Pull-ups', metric_type: 'reps', sort_order: 1 },
    ];
    const api = {
      getExercises: vi.fn().mockReturnValue(of(exercises)),
    } as any;
    const component = new ExerciseManagementComponent(api);

    component.refresh();

    expect(component.exercises).toEqual(exercises);
  });

  it('creates exercise, resets draft, and refreshes list', () => {
    const api = {
      createExercise: vi.fn().mockReturnValue(of({})),
      getExercises: vi.fn().mockReturnValue(of([])),
    } as any;
    const component = new ExerciseManagementComponent(api);
    const refreshSpy = vi.spyOn(component, 'refresh').mockImplementation(() => {});
    component.exercises = [{ id: 3, slug: 'squat', name: 'Squat', metric_type: 'reps', sort_order: 4 }];
    component.draft = { name: 'Bent Over Row', metric_type: 'reps_plus_weight_lbs' };

    component.addExercise();

    expect(api.createExercise).toHaveBeenCalledWith({ slug: 'bent-over-row', name: 'Bent Over Row', metric_type: 'reps_plus_weight_lbs', sort_order: 5 });
    expect(component.message).toBe('Exercise created');
    expect(component.draft).toEqual({ name: '', metric_type: 'reps' });
    expect(refreshSpy).toHaveBeenCalledOnce();
  });

  it('sets error message when creating exercise fails', () => {
    const api = {
      createExercise: vi.fn().mockReturnValue(throwError(() => new Error('boom'))),
    } as any;
    const component = new ExerciseManagementComponent(api);

    component.addExercise();

    expect(component.message).toBe('Failed to create exercise');
  });

  it('updates one exercise on success', () => {
    const api = {
      updateExercise: vi.fn().mockReturnValue(of({ id: 4, slug: 'squat', name: 'Back Squat', metric_type: 'reps', sort_order: 3 })),
    } as any;
    const component = new ExerciseManagementComponent(api);
    const exercise: Exercise = { id: 4, slug: 'squat', name: 'Squat', metric_type: 'reps', sort_order: 3 };

    component.saveExercise(exercise);

    expect(api.updateExercise).toHaveBeenCalledWith(4, { name: 'Squat', metric_type: 'reps', sort_order: 3 });
    expect(component.message).toBe('Exercise updated');
    expect(exercise.name).toBe('Back Squat');
  });

  it('reorders exercises when dropped and applies API response', () => {
    const exercises: Exercise[] = [
      { id: 1, slug: 'a', name: 'A', metric_type: 'reps', sort_order: 2 },
      { id: 2, slug: 'b', name: 'B', metric_type: 'reps', sort_order: 1 },
    ];
    const reordered: Exercise[] = [
      { id: 2, slug: 'b', name: 'B', metric_type: 'reps', sort_order: 1 },
      { id: 1, slug: 'a', name: 'A', metric_type: 'reps', sort_order: 2 },
    ];
    const api = {
      reorderExercises: vi.fn().mockReturnValue(of(reordered)),
    } as any;
    const component = new ExerciseManagementComponent(api);
    component.exercises = exercises;

    component.onDrop({ previousIndex: 1, currentIndex: 0 } as any);

    expect(api.reorderExercises).toHaveBeenCalledWith({
      items: [
        { id: 2, sort_order: 1 },
        { id: 1, sort_order: 2 },
      ],
    });
    expect(component.exercises).toEqual(reordered);
    expect(component.message).toBe('Order updated');
  });

  it('does not call reorder when dropped on itself', () => {
    const api = {
      reorderExercises: vi.fn(),
    } as any;
    const component = new ExerciseManagementComponent(api);
    component.exercises = [{ id: 1, slug: 'a', name: 'A', metric_type: 'reps', sort_order: 1 }];

    component.onDrop({ previousIndex: 0, currentIndex: 0 } as any);

    expect(api.reorderExercises).not.toHaveBeenCalled();
  });
});
