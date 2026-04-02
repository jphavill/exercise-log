import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIconComponent } from '@ng-icons/core';

import {
  CreateExerciseRequest,
  Exercise,
  MetricType,
  ReorderExercisesRequest,
} from '../../models/api.models';
import { ApiService } from '../../services/api/api.service';

@Component({
  selector: 'app-exercise-management',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIconComponent],
  template: `
    <section class="section">
      <h2 class="section-title"><ng-icon name="sectionTable" aria-hidden="true"></ng-icon><span>Manage Exercises</span></h2>
      <p *ngIf="message">{{ message }}</p>

      <table class="table" *ngIf="exercises.length">
        <thead>
          <tr><th>Order</th><th>Name</th><th>Slug</th><th>Metric Type</th><th>Actions</th></tr>
        </thead>
        <tbody>
          <tr
            *ngFor="let exercise of exercises; let index = index"
            draggable="true"
            (dragstart)="onDragStart(exercise.id)"
            (dragover)="onDragOver($event)"
            (drop)="onDrop(exercise.id)"
            (dragend)="onDragEnd()"
          >
            <td>{{ index + 1 }}</td>
            <td><input type="text" [(ngModel)]="exercise.name" /></td>
            <td>{{ exercise.slug }}</td>
            <td>
              <div class="metric-toggle" role="group" aria-label="Metric type">
                <button
                  type="button"
                  class="metric-option"
                  [class.selected]="exercise.metric_type === 'duration_seconds'"
                  (click)="exercise.metric_type = 'duration_seconds'"
                  aria-label="Duration"
                  title="Duration"
                >
                  <ng-icon name="metricDuration" aria-hidden="true"></ng-icon>
                </button>
                <button
                  type="button"
                  class="metric-option"
                  [class.selected]="exercise.metric_type === 'reps'"
                  (click)="exercise.metric_type = 'reps'"
                  aria-label="Reps"
                  title="Reps"
                >
                  <ng-icon name="metricReps" aria-hidden="true"></ng-icon>
                </button>
                <button
                  type="button"
                  class="metric-option"
                  [class.selected]="exercise.metric_type === 'reps_plus_weight_lbs'"
                  (click)="exercise.metric_type = 'reps_plus_weight_lbs'"
                  aria-label="Weighted reps"
                  title="Weighted reps"
                >
                  <ng-icon name="metricWeightedReps" aria-hidden="true"></ng-icon>
                </button>
              </div>
            </td>
            <td>
              <button class="button-with-icon" (click)="saveExercise(exercise)">
                <ng-icon name="actionSave" aria-hidden="true"></ng-icon>
                <span>Save</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="section">
      <h2 class="section-title"><ng-icon name="actionAdd" aria-hidden="true"></ng-icon><span>Add Exercise</span></h2>
      <form (ngSubmit)="addExercise()" #createForm="ngForm" class="form-grid">
        <input name="name" [(ngModel)]="draft.name" placeholder="Name" required />
        <input name="slug" [(ngModel)]="draft.slug" placeholder="slug-like-this" required />
        <input type="hidden" name="metricType" [(ngModel)]="draft.metric_type" required />
        <div class="metric-toggle" role="group" aria-label="Metric type">
          <button
            type="button"
            class="metric-option"
            [class.selected]="draft.metric_type === 'duration_seconds'"
            (click)="draft.metric_type = 'duration_seconds'"
            aria-label="Duration"
            title="Duration"
          >
            <ng-icon name="metricDuration" aria-hidden="true"></ng-icon>
          </button>
          <button
            type="button"
            class="metric-option"
            [class.selected]="draft.metric_type === 'reps'"
            (click)="draft.metric_type = 'reps'"
            aria-label="Reps"
            title="Reps"
          >
            <ng-icon name="metricReps" aria-hidden="true"></ng-icon>
          </button>
          <button
            type="button"
            class="metric-option"
            [class.selected]="draft.metric_type === 'reps_plus_weight_lbs'"
            (click)="draft.metric_type = 'reps_plus_weight_lbs'"
            aria-label="Weighted reps"
            title="Weighted reps"
          >
            <ng-icon name="metricWeightedReps" aria-hidden="true"></ng-icon>
          </button>
        </div>
        <input name="sortOrder" type="number" min="1" [(ngModel)]="draft.sort_order" required />
        <button class="button-with-icon" type="submit" [disabled]="createForm.invalid">
          <ng-icon name="actionAdd" aria-hidden="true"></ng-icon>
          <span>Add</span>
        </button>
      </form>
    </section>
  `,
})
export class ExerciseManagementComponent implements OnInit {
  exercises: Exercise[] = [];
  message = '';
  private draggingExerciseId: number | null = null;
  draft: CreateExerciseRequest = {
    name: '',
    slug: '',
    metric_type: 'reps',
    sort_order: 10,
  };

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.api.getExercises().subscribe((items) => (this.exercises = items));
  }

  addExercise(): void {
    this.api.createExercise(this.draft).subscribe({
      next: () => {
        this.message = 'Exercise created';
        this.draft = { name: '', slug: '', metric_type: 'reps' as MetricType, sort_order: 10 };
        this.refresh();
      },
      error: () => (this.message = 'Failed to create exercise'),
    });
  }

  saveExercise(exercise: Exercise): void {
    this.api
      .updateExercise(exercise.id, {
        name: exercise.name,
        metric_type: exercise.metric_type,
        sort_order: exercise.sort_order,
      })
      .subscribe({
        next: () => {
          this.message = 'Exercise updated';
          this.refresh();
        },
        error: () => (this.message = 'Failed to update exercise'),
      });
  }

  onDragStart(exerciseId: number): void {
    this.draggingExerciseId = exerciseId;
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
  }

  onDrop(targetExerciseId: number): void {
    if (this.draggingExerciseId === null || this.draggingExerciseId === targetExerciseId) {
      return;
    }

    const sourceIndex = this.exercises.findIndex((exercise) => exercise.id === this.draggingExerciseId);
    const targetIndex = this.exercises.findIndex((exercise) => exercise.id === targetExerciseId);
    if (sourceIndex < 0 || targetIndex < 0) {
      return;
    }

    const previousOrder = this.exercises.map((exercise) => ({ ...exercise }));
    const reordered = [...this.exercises];
    const [moved] = reordered.splice(sourceIndex, 1);
    reordered.splice(targetIndex, 0, moved);
    this.exercises = reordered.map((exercise, index) => ({ ...exercise, sort_order: index + 1 }));
    this.persistReorder(previousOrder);
  }

  onDragEnd(): void {
    this.draggingExerciseId = null;
  }

  private persistReorder(previousOrder: Exercise[]): void {
    const payload: ReorderExercisesRequest = {
      items: this.exercises.map((exercise) => ({ id: exercise.id, sort_order: exercise.sort_order })),
    };
    this.api.reorderExercises(payload).subscribe({
      next: (items) => {
        this.exercises = items;
        this.message = 'Order updated';
      },
      error: () => {
        this.exercises = previousOrder;
        this.message = 'Failed to reorder exercises';
      },
    });
  }
}
