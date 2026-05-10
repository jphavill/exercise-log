import { CdkDragDrop, DragDropModule, moveItemInArray } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { NgIconComponent } from '@ng-icons/core';

import {
  Workout,
  WorkoutDefinition,
  WorkoutDefinitionItem,
  WorkoutStep,
} from '../../models/api.models';
import { ApiService } from '../../services/api/api.service';

type WorkoutDraftMode = 'edit' | 'new' | 'copy';

interface WorkoutDraft {
  id: number | null;
  mode: WorkoutDraftMode;
  name: string;
  enabled: boolean;
  sort_order: number;
  definitionJson: string;
}

interface DraftValidation {
  valid: boolean;
  message: string;
  durationMin: number;
  definition: WorkoutDefinition | null;
}

@Component({
  selector: 'app-workouts',
  standalone: true,
  imports: [CommonModule, DragDropModule, FormsModule, NgIconComponent],
  templateUrl: './workouts.component.html',
  styleUrl: './workouts.component.css',
})
export class WorkoutsComponent implements OnInit {
  workouts: Workout[] = [];
  workoutDefinitions: WorkoutDefinitionItem[] = [];
  hasLoaded = false;
  editMode = false;
  message = '';
  openMenuWorkoutId: number | null = null;
  editorDraft: WorkoutDraft | null = null;
  deleteCandidate: WorkoutDefinitionItem | null = null;
  isSaving = false;

  constructor(
    private readonly api: ApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.refreshPublicWorkouts();
  }

  @HostListener('document:click')
  onDocumentClick(): void {
    this.openMenuWorkoutId = null;
  }

  setEditMode(enabled: boolean): void {
    if (this.editMode === enabled) {
      return;
    }

    this.editMode = enabled;
    this.message = '';
    this.openMenuWorkoutId = null;
    if (enabled) {
      this.refreshEditorWorkouts();
      return;
    }

    this.editorDraft = null;
    this.deleteCandidate = null;
    this.refreshPublicWorkouts();
  }

  selectWorkout(workout: Workout): void {
    if (this.editMode) {
      return;
    }

    void this.router.navigate(['/workouts', workout.id]);
  }

  toggleMenu(workoutId: number, event: MouseEvent): void {
    event.stopPropagation();
    this.openMenuWorkoutId = this.openMenuWorkoutId === workoutId ? null : workoutId;
  }

  onMenuClick(event: MouseEvent): void {
    event.stopPropagation();
  }

  editWorkout(workout: WorkoutDefinitionItem): void {
    this.openMenuWorkoutId = null;
    this.editorDraft = this.createDraftFromWorkout(workout, 'edit');
  }

  copyWorkout(workout: WorkoutDefinitionItem): void {
    this.openMenuWorkoutId = null;
    this.editorDraft = this.createDraftFromWorkout(workout, 'copy', `Copy - ${workout.name}`, false, this.getNextSortOrder());
  }

  startNewWorkout(): void {
    this.openMenuWorkoutId = null;
    this.editorDraft = {
      id: null,
      mode: 'new',
      name: 'New Workout',
      enabled: false,
      sort_order: this.getNextSortOrder(),
      definitionJson: JSON.stringify(
        {
          steps: [{ kind: 'timed_exercise', title: 'Exercise', duration_sec: 30 }],
        },
        null,
        2,
      ),
    };
  }

  requestDelete(workout: WorkoutDefinitionItem): void {
    this.openMenuWorkoutId = null;
    this.deleteCandidate = workout;
  }

  cancelDelete(): void {
    this.deleteCandidate = null;
  }

  confirmDelete(): void {
    if (!this.deleteCandidate) {
      return;
    }

    const workout = this.deleteCandidate;
    this.api.deleteWorkout(workout.id).subscribe({
      next: () => {
        this.message = 'Workout deleted';
        this.deleteCandidate = null;
        if (this.editorDraft?.id === workout.id) {
          this.editorDraft = null;
        }
        this.refreshEditorWorkouts();
      },
      error: () => (this.message = 'Failed to delete workout'),
    });
  }

  toggleWorkoutEnabled(workout: WorkoutDefinitionItem, event: Event): void {
    event.stopPropagation();
    const checkbox = event.target as HTMLInputElement;
    const enabled = checkbox.checked;
    const previous = workout.enabled;
    workout.enabled = enabled;

    this.api.updateWorkoutEnabled(workout.id, { enabled }).subscribe({
      next: (updated) => {
        Object.assign(workout, updated);
        this.message = updated.enabled ? 'Workout enabled' : 'Workout disabled';
      },
      error: () => {
        workout.enabled = previous;
        checkbox.checked = previous;
        this.message = 'Failed to update workout';
      },
    });
  }

  onDrop(event: CdkDragDrop<WorkoutDefinitionItem[]>): void {
    if (!this.editMode || event.previousIndex === event.currentIndex) {
      return;
    }

    const previousOrder = this.workoutDefinitions.map((workout) => ({
      ...workout,
      definition: { steps: [...workout.definition.steps] },
    }));
    const reordered = [...this.workoutDefinitions];
    moveItemInArray(reordered, event.previousIndex, event.currentIndex);
    this.workoutDefinitions = reordered.map((workout, index) => ({ ...workout, sort_order: index + 1 }));

    this.api
      .reorderWorkouts({
        items: this.workoutDefinitions.map((workout) => ({ id: workout.id, sort_order: workout.sort_order })),
      })
      .subscribe({
        next: (workouts) => {
          this.workoutDefinitions = workouts;
          this.message = 'Order updated';
        },
        error: () => {
          this.workoutDefinitions = previousOrder;
          this.message = 'Failed to reorder workouts';
        },
      });
  }

  saveDraft(): void {
    const draft = this.editorDraft;
    const validation = this.validateDraft();
    if (!draft || !validation.valid || !validation.definition || this.isSaving) {
      return;
    }

    this.isSaving = true;
    const payload = {
      name: draft.name.trim(),
      enabled: draft.enabled,
      sort_order: Number(draft.sort_order),
      definition: validation.definition,
    };
    const request = draft.id
      ? this.api.updateWorkout(draft.id, payload)
      : this.api.createWorkout(payload);

    request.subscribe({
      next: (saved) => {
        this.isSaving = false;
        this.message = draft.id ? 'Workout updated' : 'Workout created';
        this.editorDraft = this.createDraftFromWorkout(saved, 'edit');
        this.refreshEditorWorkouts();
      },
      error: () => {
        this.isSaving = false;
        this.message = 'Failed to save workout';
      },
    });
  }

  cancelEdit(): void {
    this.editorDraft = null;
  }

  canSaveDraft(): boolean {
    return !this.isSaving && this.validateDraft().valid;
  }

  get draftValidation(): DraftValidation {
    return this.validateDraft();
  }

  trackByWorkoutId(_: number, workout: Workout): number {
    return workout.id;
  }

  trackByDefinitionWorkoutId(_: number, workout: WorkoutDefinitionItem): number {
    return workout.id;
  }

  private refreshPublicWorkouts(): void {
    this.hasLoaded = false;
    this.api.getWorkouts().subscribe({
      next: (workouts) => {
        this.workouts = workouts;
        this.hasLoaded = true;
      },
      error: () => {
        this.workouts = [];
        this.hasLoaded = true;
        this.message = 'Failed to load workouts';
      },
    });
  }

  private refreshEditorWorkouts(): void {
    this.hasLoaded = false;
    this.api.getWorkoutDefinitions().subscribe({
      next: (workouts) => {
        this.workoutDefinitions = workouts;
        this.hasLoaded = true;
      },
      error: () => {
        this.workoutDefinitions = [];
        this.hasLoaded = true;
        this.message = 'Failed to load workout editor';
      },
    });
  }

  private createDraftFromWorkout(
    workout: WorkoutDefinitionItem,
    mode: WorkoutDraftMode,
    name = workout.name,
    enabled = workout.enabled,
    sortOrder = workout.sort_order,
  ): WorkoutDraft {
    return {
      id: mode === 'edit' ? workout.id : null,
      mode,
      name,
      enabled,
      sort_order: sortOrder,
      definitionJson: JSON.stringify(workout.definition, null, 2),
    };
  }

  private getNextSortOrder(): number {
    if (this.workoutDefinitions.length === 0) {
      return 1;
    }

    return Math.max(...this.workoutDefinitions.map((workout) => workout.sort_order)) + 1;
  }

  private validateDraft(): DraftValidation {
    const draft = this.editorDraft;
    if (!draft) {
      return { valid: false, message: 'No workout selected.', durationMin: 1, definition: null };
    }
    if (!draft.name.trim()) {
      return { valid: false, message: 'Name is required.', durationMin: 1, definition: null };
    }
    if (!Number.isInteger(Number(draft.sort_order)) || Number(draft.sort_order) < 0) {
      return { valid: false, message: 'Sort order must be a whole number 0 or greater.', durationMin: 1, definition: null };
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(draft.definitionJson);
    } catch {
      return { valid: false, message: 'Definition JSON is invalid.', durationMin: 1, definition: null };
    }

    const stepValidation = this.validateDefinition(parsed);
    if (!stepValidation.definition) {
      return stepValidation;
    }

    return {
      valid: true,
      message: 'Definition is valid.',
      durationMin: this.calculateDurationMin(stepValidation.definition.steps),
      definition: stepValidation.definition,
    };
  }

  private validateDefinition(value: unknown): DraftValidation {
    if (!this.isRecord(value) || !Array.isArray(value['steps'])) {
      return { valid: false, message: 'Definition must include a steps array.', durationMin: 1, definition: null };
    }
    if (value['steps'].length === 0) {
      return { valid: false, message: 'Definition must include at least one step.', durationMin: 1, definition: null };
    }

    const steps: WorkoutStep[] = [];
    for (const step of value['steps']) {
      const validStep = this.validateStep(step);
      if (!validStep) {
        return { valid: false, message: 'Each step must match a supported workout step schema.', durationMin: 1, definition: null };
      }
      steps.push(validStep);
    }

    const definition = { steps };
    return {
      valid: true,
      message: 'Definition is valid.',
      durationMin: this.calculateDurationMin(steps),
      definition,
    };
  }

  private validateStep(value: unknown): WorkoutStep | null {
    if (!this.isRecord(value) || typeof value['title'] !== 'string' || !value['title'].trim()) {
      return null;
    }

    const title = value['title'].trim();
    if (value['kind'] === 'timed_exercise' || value['kind'] === 'rest') {
      const durationSec = Number(value['duration_sec']);
      if (!Number.isInteger(durationSec) || durationSec <= 0) {
        return null;
      }
      return { kind: value['kind'], title, duration_sec: durationSec };
    }

    if (value['kind'] === 'rep_exercise') {
      const reps = Number(value['reps']);
      if (!Number.isInteger(reps) || reps <= 0 || typeof value['rep_unit'] !== 'string' || !value['rep_unit'].trim()) {
        return null;
      }
      return { kind: 'rep_exercise', title, reps, rep_unit: value['rep_unit'].trim() };
    }

    return null;
  }

  private calculateDurationMin(steps: WorkoutStep[]): number {
    const totalSeconds = steps.reduce((total, step) => {
      if (step.kind === 'timed_exercise' || step.kind === 'rest') {
        return total + step.duration_sec;
      }
      return total;
    }, 0);
    return Math.max(1, Math.ceil(totalSeconds / 60));
  }

  private isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null;
  }
}
