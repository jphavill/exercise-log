import { describe, expect, it, vi } from 'vitest';
import { of, throwError } from 'rxjs';

import { ExerciseManagementComponent } from './exercise-management.component';
import { Exercise } from '../../models/api.models';

describe('ExerciseManagementComponent', () => {
  it('loads exercises during refresh', () => {
    const exercises: Exercise[] = [
      {
        id: 1,
        slug: 'pull-ups',
        name: 'Pull-ups',
        metric_type: 'reps',
        sort_order: 1,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
    ];
    const api = {
      getExercises: vi.fn().mockReturnValue(of(exercises)),
    } as any;
    const component = new ExerciseManagementComponent(api);

    component.refresh();

    expect(component.exercises).toEqual(exercises);
  });

  it('adds one pending row with default metric', () => {
    const api = {} as any;
    const component = new ExerciseManagementComponent(api);

    component.addPendingExerciseRow();
    component.addPendingExerciseRow();

    expect(component.pendingExercise).toEqual({
      name: '',
      metric_type: 'reps',
      goal_reps: null,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    });
  });

  it('creates pending exercise, resets row, and refreshes list', () => {
    const api = {
      createExercise: vi.fn().mockReturnValue(of({})),
      getExercises: vi.fn().mockReturnValue(of([])),
    } as any;
    const component = new ExerciseManagementComponent(api);
    const refreshSpy = vi.spyOn(component, 'refresh').mockImplementation(() => {});
    component.exercises = [
      {
        id: 3,
        slug: 'squat',
        name: 'Squat',
        metric_type: 'reps',
        sort_order: 4,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
    ];
    component.pendingExercise = {
      name: 'Bent Over Row',
      metric_type: 'reps_plus_weight_lbs',
      goal_reps: 30,
      goal_duration_seconds: null,
      goal_weight_lbs: 25,
    };

    component.savePendingExercise();

    expect(api.createExercise).toHaveBeenCalledWith({
      slug: 'bent-over-row',
      name: 'Bent Over Row',
      metric_type: 'reps_plus_weight_lbs',
      sort_order: 5,
      goal_reps: 30,
      goal_duration_seconds: null,
      goal_weight_lbs: 25,
    });
    expect(component.message).toBe('Exercise created');
    expect(component.pendingExercise).toBeNull();
    expect(refreshSpy).toHaveBeenCalledOnce();
  });

  it('does not create pending exercise when name is blank', () => {
    const api = {
      createExercise: vi.fn(),
    } as any;
    const component = new ExerciseManagementComponent(api);
    component.pendingExercise = {
      name: '   ',
      metric_type: 'reps',
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    };

    component.savePendingExercise();

    expect(api.createExercise).not.toHaveBeenCalled();
  });

  it('sets error message when creating pending exercise fails', () => {
    const api = {
      createExercise: vi.fn().mockReturnValue(throwError(() => new Error('boom'))),
    } as any;
    const component = new ExerciseManagementComponent(api);
    component.pendingExercise = {
      name: 'Front Lever',
      metric_type: 'duration_seconds',
      goal_reps: null,
      goal_duration_seconds: 40,
      goal_weight_lbs: null,
    };

    component.savePendingExercise();

    expect(component.message).toBe('Failed to create exercise');
  });

  it('deletes exercise and refreshes list', () => {
    const api = {
      deleteExercise: vi.fn().mockReturnValue(of(undefined)),
    } as any;
    const component = new ExerciseManagementComponent(api);
    const refreshSpy = vi.spyOn(component, 'refresh').mockImplementation(() => {});

    component.deleteExercise(8);

    expect(api.deleteExercise).toHaveBeenCalledWith(8);
    expect(component.message).toBe('Exercise deleted');
    expect(refreshSpy).toHaveBeenCalledOnce();
  });

  it('updates one exercise on success', () => {
    const api = {
      updateExercise: vi.fn().mockReturnValue(
        of({
          id: 4,
          slug: 'squat',
          name: 'Back Squat',
          metric_type: 'reps',
          sort_order: 3,
          goal_reps: 40,
          goal_duration_seconds: null,
          goal_weight_lbs: null,
        }),
      ),
    } as any;
    const component = new ExerciseManagementComponent(api);
    const exercise: Exercise = {
      id: 4,
      slug: 'squat',
      name: 'Squat',
      metric_type: 'reps',
      sort_order: 3,
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    };

    component.saveExercise(exercise);

    expect(api.updateExercise).toHaveBeenCalledWith(4, {
      name: 'Squat',
      metric_type: 'reps',
      sort_order: 3,
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    });
    expect(component.message).toBe('Exercise updated');
    expect(exercise.name).toBe('Back Squat');
  });

  it('reorders exercises when dropped and applies API response', () => {
    const exercises: Exercise[] = [
      {
        id: 1,
        slug: 'a',
        name: 'A',
        metric_type: 'reps',
        sort_order: 2,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
      {
        id: 2,
        slug: 'b',
        name: 'B',
        metric_type: 'reps',
        sort_order: 1,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
    ];
    const reordered: Exercise[] = [
      {
        id: 2,
        slug: 'b',
        name: 'B',
        metric_type: 'reps',
        sort_order: 1,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
      {
        id: 1,
        slug: 'a',
        name: 'A',
        metric_type: 'reps',
        sort_order: 2,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
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
    component.exercises = [
      {
        id: 1,
        slug: 'a',
        name: 'A',
        metric_type: 'reps',
        sort_order: 1,
        goal_reps: 40,
        goal_duration_seconds: null,
        goal_weight_lbs: null,
      },
    ];

    component.onDrop({ previousIndex: 0, currentIndex: 0 } as any);

    expect(api.reorderExercises).not.toHaveBeenCalled();
  });

  it('clears goal fields when metric type changes', () => {
    const component = new ExerciseManagementComponent({} as any);
    const exercise: Exercise = {
      id: 1,
      slug: 'weighted-pullups',
      name: 'Weighted Pull-ups',
      metric_type: 'reps_plus_weight_lbs',
      sort_order: 1,
      goal_reps: 40,
      goal_duration_seconds: null,
      goal_weight_lbs: 15,
    };

    component.updateMetricType(exercise, 'duration_seconds');

    expect(exercise.metric_type).toBe('duration_seconds');
    expect(exercise.goal_reps).toBeNull();
    expect(exercise.goal_duration_seconds).toBeNull();
    expect(exercise.goal_weight_lbs).toBeNull();
  });

  it('enters goal edit mode when add goal is selected', () => {
    const component = new ExerciseManagementComponent({} as any);
    const exercise: Exercise = {
      id: 2,
      slug: 'plank',
      name: 'Plank',
      metric_type: 'duration_seconds',
      sort_order: 2,
      goal_reps: null,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    };
    component.openMenuExerciseId = exercise.id;

    component.addGoal(exercise);

    expect(component.goalEditExerciseId).toBe(exercise.id);
    expect(component.showGoalInput(exercise)).toBe(true);
    expect(component.openMenuExerciseId).toBeNull();
  });

  it('clears goal and saves exercise immediately', () => {
    const api = {
      updateExercise: vi.fn().mockReturnValue(
        of({
          id: 4,
          slug: 'squat',
          name: 'Back Squat',
          metric_type: 'reps_plus_weight_lbs',
          sort_order: 3,
          goal_reps: null,
          goal_duration_seconds: null,
          goal_weight_lbs: null,
        }),
      ),
    } as any;
    const component = new ExerciseManagementComponent(api);
    const exercise: Exercise = {
      id: 4,
      slug: 'squat',
      name: 'Back Squat',
      metric_type: 'reps_plus_weight_lbs',
      sort_order: 3,
      goal_reps: 8,
      goal_duration_seconds: null,
      goal_weight_lbs: 135,
    };

    component.clearGoal(exercise);

    expect(exercise.goal_reps).toBeNull();
    expect(exercise.goal_duration_seconds).toBeNull();
    expect(exercise.goal_weight_lbs).toBeNull();
    expect(api.updateExercise).toHaveBeenCalledWith(4, {
      name: 'Back Squat',
      metric_type: 'reps_plus_weight_lbs',
      sort_order: 3,
      goal_reps: null,
      goal_duration_seconds: null,
      goal_weight_lbs: null,
    });
    expect(component.showGoalInput(exercise)).toBe(false);
  });
});
