import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CreateExerciseRequest,
  DashboardSummary,
  Exercise,
  ExerciseHistory,
  ExerciseLog,
  ReorderExercisesRequest,
  UpdateExerciseRequest,
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
}
