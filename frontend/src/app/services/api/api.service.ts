import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import {
  CreateWorkoutRequest,
  CreateExerciseRequest,
  DashboardSummary,
  Exercise,
  ExerciseHistory,
  ExerciseLog,
  ReorderExercisesRequest,
  ReorderWorkoutsRequest,
  UpdateExerciseRequest,
  UpdateWorkoutEnabledRequest,
  UpdateWorkoutRequest,
  Workout,
  WorkoutDefinitionItem,
  WorkoutStep,
} from '../../models/api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private readonly http: HttpClient) {}

  getExercises(): Observable<Exercise[]> {
    return this.http.get<Exercise[]>('/api/exercises');
  }

  createExercise(payload: CreateExerciseRequest): Observable<Exercise> {
    return this.http.post<Exercise>('/api/exercises', payload);
  }

  updateExercise(id: number, payload: UpdateExerciseRequest): Observable<Exercise> {
    return this.http.put<Exercise>(`/api/exercises/${id}`, payload);
  }

  deleteExercise(id: number): Observable<void> {
    return this.http.delete<void>(`/api/exercises/${id}`);
  }

  reorderExercises(payload: ReorderExercisesRequest): Observable<Exercise[]> {
    return this.http.put<Exercise[]>('/api/exercises/reorder', payload);
  }

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>('/api/dashboard/summary');
  }

  getExerciseHistory(slug: string, days = 30): Observable<ExerciseHistory> {
    return this.http.get<ExerciseHistory>(`/api/exercises/${slug}/history?days=${days}`);
  }

  getRecentLogs(limit = 50): Observable<ExerciseLog[]> {
    return this.http.get<ExerciseLog[]>(`/api/logs/recent?limit=${limit}`);
  }

  deleteLog(id: number): Observable<void> {
    return this.http.delete<void>(`/api/logs/${id}`);
  }

  getWorkouts(): Observable<Workout[]> {
    return this.http.get<unknown>('/api/workouts').pipe(map(validateWorkoutsResponse));
  }

  getWorkout(id: number): Observable<Workout> {
    return this.http.get<unknown>(`/api/workouts/${id}`).pipe(map(validateWorkoutResponse));
  }

  getWorkoutDefinitions(): Observable<WorkoutDefinitionItem[]> {
    return this.http
      .get<unknown>('/api/workouts?include_disabled=true&detail=definition')
      .pipe(map(validateWorkoutDefinitionsResponse));
  }

  getWorkoutDefinition(id: number): Observable<WorkoutDefinitionItem> {
    return this.http
      .get<unknown>(`/api/workouts/${id}?include_disabled=true&detail=definition`)
      .pipe(map(validateWorkoutDefinitionResponse));
  }

  createWorkout(payload: CreateWorkoutRequest): Observable<WorkoutDefinitionItem> {
    return this.http.post<WorkoutDefinitionItem>('/api/workouts', payload);
  }

  updateWorkout(id: number, payload: UpdateWorkoutRequest): Observable<WorkoutDefinitionItem> {
    return this.http.put<WorkoutDefinitionItem>(`/api/workouts/${id}`, payload);
  }

  updateWorkoutEnabled(id: number, payload: UpdateWorkoutEnabledRequest): Observable<WorkoutDefinitionItem> {
    return this.http.patch<WorkoutDefinitionItem>(`/api/workouts/${id}/enabled`, payload);
  }

  reorderWorkouts(payload: ReorderWorkoutsRequest): Observable<WorkoutDefinitionItem[]> {
    return this.http
      .put<unknown>('/api/workouts/reorder', payload)
      .pipe(map(validateWorkoutDefinitionsResponse));
  }

  deleteWorkout(id: number): Observable<void> {
    return this.http.delete<void>(`/api/workouts/${id}`);
  }
}

function validateWorkoutResponse(response: unknown): Workout {
  const workout = isRecord(response) && isRecord(response['workout']) ? response['workout'] : response;
  return validateWorkout(workout);
}

function validateWorkoutsResponse(response: unknown): Workout[] {
  const workouts = Array.isArray(response)
    ? response
    : isRecord(response) && Array.isArray(response['workouts'])
      ? response['workouts']
      : null;

  if (!workouts) {
    throw invalidWorkoutsPayload();
  }

  return workouts.map(validateWorkout);
}

function validateWorkout(value: unknown): Workout {
  if (!isRecord(value)) {
    throw invalidWorkoutsPayload();
  }

  const id = value['id'];
  const name = value['name'];
  const durationMin = value['duration_min'];
  const steps = value['steps'];

  if (!isFiniteNumber(id) || !isNonEmptyString(name) || !isFiniteNumber(durationMin) || !Array.isArray(steps) || steps.length === 0) {
    throw invalidWorkoutsPayload();
  }

  return {
    id,
    name: name.trim(),
    duration_min: durationMin,
    steps: steps.map(validateWorkoutStep),
  };
}

function validateWorkoutDefinitionResponse(response: unknown): WorkoutDefinitionItem {
  return validateWorkoutDefinitionItem(response);
}

function validateWorkoutDefinitionsResponse(response: unknown): WorkoutDefinitionItem[] {
  const workouts = isRecord(response) && Array.isArray(response['workouts']) ? response['workouts'] : null;

  if (!workouts) {
    throw invalidWorkoutsPayload();
  }

  return workouts.map(validateWorkoutDefinitionItem);
}

function validateWorkoutDefinitionItem(value: unknown): WorkoutDefinitionItem {
  if (!isRecord(value)) {
    throw invalidWorkoutsPayload();
  }

  const id = value['id'];
  const name = value['name'];
  const durationMin = value['duration_min'];
  const enabled = value['enabled'];
  const sortOrder = value['sort_order'];
  const updatedAt = value['updated_at'];
  const definition = value['definition'];

  if (
    !isFiniteNumber(id) ||
    !isNonEmptyString(name) ||
    !isFiniteNumber(durationMin) ||
    typeof enabled !== 'boolean' ||
    !isFiniteNumber(sortOrder) ||
    !isNonEmptyString(updatedAt) ||
    !isRecord(definition) ||
    !Array.isArray(definition['steps']) ||
    definition['steps'].length === 0
  ) {
    throw invalidWorkoutsPayload();
  }

  return {
    id,
    name: name.trim(),
    duration_min: durationMin,
    enabled,
    sort_order: sortOrder,
    updated_at: updatedAt.trim(),
    definition: {
      steps: definition['steps'].map(validateWorkoutStep),
    },
  };
}

function validateWorkoutStep(value: unknown): WorkoutStep {
  if (!isRecord(value)) {
    throw invalidWorkoutsPayload();
  }

  const kind = value['kind'];
  const title = value['title'];

  if (!isNonEmptyString(title)) {
    throw invalidWorkoutsPayload();
  }

  if (kind === 'timed_exercise' || kind === 'rest') {
    const durationSec = value['duration_sec'];
    if (!isPositiveNumber(durationSec)) {
      throw invalidWorkoutsPayload();
    }

    return {
      kind,
      title: title.trim(),
      duration_sec: durationSec,
    };
  }

  if (kind === 'rep_exercise') {
    const reps = value['reps'];
    const repUnit = value['rep_unit'];
    if (!isPositiveNumber(reps) || !isNonEmptyString(repUnit)) {
      throw invalidWorkoutsPayload();
    }

    return {
      kind,
      title: title.trim(),
      reps,
      rep_unit: repUnit.trim(),
    };
  }

  throw invalidWorkoutsPayload();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isPositiveNumber(value: unknown): value is number {
  return isFiniteNumber(value) && value > 0;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function invalidWorkoutsPayload(): Error {
  return new Error('Invalid workouts payload');
}
