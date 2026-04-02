import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { CdkDragDrop, DragDropModule, moveItemInArray } from '@angular/cdk/drag-drop';
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
  imports: [CommonModule, DragDropModule, FormsModule, NgIconComponent],
  templateUrl: './exercise-management.component.html',
  styleUrl: './exercise-management.component.css',
})
export class ExerciseManagementComponent implements OnInit {
  exercises: Exercise[] = [];
  message = '';
  openMenuExerciseId: number | null = null;
  pendingExercise: { name: string; metric_type: MetricType } | null = null;
  private autosaveTimers = new Map<number, ReturnType<typeof setTimeout>>();

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.api.getExercises().subscribe((items) => (this.exercises = items));
  }

  @HostListener('document:click')
  onDocumentClick(): void {
    this.openMenuExerciseId = null;
  }

  toggleMenu(exerciseId: number, event: MouseEvent): void {
    event.stopPropagation();
    this.openMenuExerciseId = this.openMenuExerciseId === exerciseId ? null : exerciseId;
  }

  onMenuClick(event: MouseEvent): void {
    event.stopPropagation();
  }

  addPendingExerciseRow(): void {
    this.openMenuExerciseId = null;
    if (this.pendingExercise) {
      return;
    }

    this.pendingExercise = {
      name: '',
      metric_type: 'reps',
    };
  }

  savePendingExercise(): void {
    if (!this.pendingExercise || !this.pendingExercise.name.trim()) {
      return;
    }

    const name = this.pendingExercise.name.trim();
    const payload: CreateExerciseRequest = {
      ...this.pendingExercise,
      name,
      slug: this.buildSlug(name),
      sort_order: this.getNextSortOrder(),
    };

    this.api.createExercise(payload).subscribe({
      next: () => {
        this.message = 'Exercise created';
        this.pendingExercise = null;
        this.refresh();
      },
      error: () => (this.message = 'Failed to create exercise'),
    });
  }

  deleteExercise(exerciseId: number): void {
    this.openMenuExerciseId = null;
    this.api.deleteExercise(exerciseId).subscribe({
      next: () => {
        this.message = 'Exercise deleted';
        this.refresh();
      },
      error: () => (this.message = 'Failed to delete exercise'),
    });
  }

  saveExercise(exercise: Exercise): void {
    this.clearAutosaveTimer(exercise.id);
    this.api
      .updateExercise(exercise.id, {
        name: exercise.name,
        metric_type: exercise.metric_type,
        sort_order: exercise.sort_order,
      })
      .subscribe({
        next: (updated) => {
          Object.assign(exercise, updated);
          this.message = 'Exercise updated';
        },
        error: () => (this.message = 'Failed to update exercise'),
      });
  }

  queueExerciseAutosave(exercise: Exercise): void {
    this.clearAutosaveTimer(exercise.id);
    this.autosaveTimers.set(
      exercise.id,
      setTimeout(() => {
        this.saveExercise(exercise);
      }, 450),
    );
  }

  updateMetricType(exercise: Exercise, metricType: MetricType): void {
    if (exercise.metric_type === metricType) {
      return;
    }

    exercise.metric_type = metricType;
    this.saveExercise(exercise);
  }

  onDrop(event: CdkDragDrop<Exercise[]>): void {
    if (event.previousIndex === event.currentIndex) {
      return;
    }

    const previousOrder = this.exercises.map((exercise) => ({ ...exercise }));
    const reordered = [...this.exercises];
    moveItemInArray(reordered, event.previousIndex, event.currentIndex);
    this.exercises = reordered.map((exercise, index) => ({ ...exercise, sort_order: index + 1 }));
    this.persistReorder(previousOrder);
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

  private clearAutosaveTimer(exerciseId: number): void {
    const timer = this.autosaveTimers.get(exerciseId);
    if (!timer) {
      return;
    }

    clearTimeout(timer);
    this.autosaveTimers.delete(exerciseId);
  }

  private getNextSortOrder(): number {
    if (this.exercises.length === 0) {
      return 1;
    }

    return Math.max(...this.exercises.map((exercise) => exercise.sort_order)) + 1;
  }

  private buildSlug(name: string): string {
    return name.toLowerCase().replaceAll(' ', '-');
  }
}
