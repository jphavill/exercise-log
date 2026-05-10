import { describe, expect, it, vi } from 'vitest';
import { of, throwError } from 'rxjs';

import { WorkoutDefinitionItem } from '../../models/api.models';
import { WorkoutsComponent } from './workouts.component';

const definitionWorkout: WorkoutDefinitionItem = {
  id: 1,
  name: 'Grip Circuit',
  duration_min: 2,
  enabled: true,
  sort_order: 1,
  updated_at: '2026-05-10T12:00:00Z',
  definition: {
    steps: [
      { kind: 'timed_exercise', title: 'Hang', duration_sec: 61 },
      { kind: 'rep_exercise', title: 'Pull-ups', reps: 5, rep_unit: 'reps' },
    ],
  },
};

describe('WorkoutsComponent', () => {
  it('loads public workouts on init and navigates in normal mode', () => {
    const workouts = [{ id: 1, name: 'Grip Circuit', duration_min: 2, steps: definitionWorkout.definition.steps }];
    const api = { getWorkouts: vi.fn().mockReturnValue(of(workouts)) } as any;
    const router = { navigate: vi.fn() } as any;
    const component = new WorkoutsComponent(api, router);

    component.ngOnInit();
    component.selectWorkout(workouts[0]);

    expect(component.workouts).toEqual(workouts);
    expect(component.hasLoaded).toBe(true);
    expect(router.navigate).toHaveBeenCalledWith(['/workouts', 1]);
  });

  it('loads definition workouts when edit mode is enabled', () => {
    const api = { getWorkoutDefinitions: vi.fn().mockReturnValue(of([definitionWorkout])) } as any;
    const component = new WorkoutsComponent(api, {} as any);

    component.setEditMode(true);

    expect(component.editMode).toBe(true);
    expect(component.workoutDefinitions).toEqual([definitionWorkout]);
    expect(api.getWorkoutDefinitions).toHaveBeenCalledOnce();
  });

  it('builds new and copied drafts with expected defaults', () => {
    const component = new WorkoutsComponent({} as any, {} as any);
    component.workoutDefinitions = [definitionWorkout];

    component.startNewWorkout();
    expect(component.editorDraft).toMatchObject({ name: 'New Workout', enabled: false, sort_order: 2 });
    expect(component.draftValidation.valid).toBe(true);
    expect(component.draftValidation.durationMin).toBe(1);

    component.copyWorkout(definitionWorkout);
    expect(component.editorDraft).toMatchObject({ name: 'Copy - Grip Circuit', enabled: false, sort_order: 2, id: null });
  });

  it('validates draft JSON and saves valid drafts', () => {
    const saved = { ...definitionWorkout, id: 2, name: 'Saved', duration_min: 2 };
    const api = {
      createWorkout: vi.fn().mockReturnValue(of(saved)),
      getWorkoutDefinitions: vi.fn().mockReturnValue(of([saved])),
    } as any;
    const component = new WorkoutsComponent(api, {} as any);
    component.editorDraft = {
      id: null,
      mode: 'new',
      name: ' Saved ',
      enabled: false,
      sort_order: 3,
      definitionJson: JSON.stringify({ steps: [{ kind: 'rest', title: 'Rest', duration_sec: 90 }] }),
    };

    component.saveDraft();

    expect(api.createWorkout).toHaveBeenCalledWith({
      name: 'Saved',
      enabled: false,
      sort_order: 3,
      definition: { steps: [{ kind: 'rest', title: 'Rest', duration_sec: 90 }] },
    });
    expect(component.message).toBe('Workout created');
    expect(component.editorDraft?.id).toBe(2);
  });

  it('does not save invalid draft JSON', () => {
    const api = { createWorkout: vi.fn() } as any;
    const component = new WorkoutsComponent(api, {} as any);
    component.editorDraft = {
      id: null,
      mode: 'new',
      name: 'Invalid',
      enabled: false,
      sort_order: 1,
      definitionJson: '{',
    };

    component.saveDraft();

    expect(component.draftValidation.valid).toBe(false);
    expect(component.draftValidation.message).toBe('Definition JSON is invalid.');
    expect(api.createWorkout).not.toHaveBeenCalled();
  });

  it('reorders editor workouts and restores previous order on failure', () => {
    const second = { ...definitionWorkout, id: 2, name: 'Second', sort_order: 2 };
    const api = { reorderWorkouts: vi.fn().mockReturnValue(throwError(() => new Error('boom'))) } as any;
    const component = new WorkoutsComponent(api, {} as any);
    component.editMode = true;
    component.workoutDefinitions = [definitionWorkout, second];

    component.onDrop({ previousIndex: 1, currentIndex: 0 } as any);

    expect(api.reorderWorkouts).toHaveBeenCalledWith({
      items: [
        { id: 2, sort_order: 1 },
        { id: 1, sort_order: 2 },
      ],
    });
    expect(component.workoutDefinitions.map((workout) => workout.id)).toEqual([1, 2]);
    expect(component.message).toBe('Failed to reorder workouts');
  });

  it('toggles enabled and deletes workouts through editor endpoints', () => {
    const api = {
      updateWorkoutEnabled: vi.fn().mockReturnValue(of({ ...definitionWorkout, enabled: false })),
      deleteWorkout: vi.fn().mockReturnValue(of(undefined)),
      getWorkoutDefinitions: vi.fn().mockReturnValue(of([])),
    } as any;
    const component = new WorkoutsComponent(api, {} as any);
    const checkbox = { checked: false } as HTMLInputElement;
    const event = { stopPropagation: vi.fn(), target: checkbox } as any;

    component.toggleWorkoutEnabled(definitionWorkout, event);
    component.requestDelete(definitionWorkout);
    component.confirmDelete();

    expect(api.updateWorkoutEnabled).toHaveBeenCalledWith(1, { enabled: false });
    expect(api.deleteWorkout).toHaveBeenCalledWith(1);
    expect(component.deleteCandidate).toBeNull();
  });
});
