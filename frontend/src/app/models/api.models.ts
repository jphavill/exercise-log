export type MetricType = 'duration_seconds' | 'reps' | 'reps_plus_weight_lbs';

export interface Totals {
  reps: number | null;
  duration_seconds: number | null;
}

export interface Exercise {
  id: number;
  slug: string;
  name: string;
  metric_type: MetricType;
  sort_order: number;
}

export interface ExerciseLog {
  id: number;
  exercise_slug: string;
  exercise_name: string;
  metric_type: MetricType;
  reps: number | null;
  duration_seconds: number | null;
  weight_lbs: number | null;
  notes: string | null;
  logged_at: string;
}

export interface ExerciseTotalsItem {
  exercise_id: number;
  exercise_slug: string;
  exercise_name: string;
  metric_type: MetricType;
  totals: Totals;
}

export interface DashboardSummary {
  today: ExerciseTotalsItem[];
  current_week: ExerciseTotalsItem[];
  last_30_days: ExerciseTotalsItem[];
  total_logs_today: number;
  total_logs_this_week: number;
}

export interface DailyTotalItem {
  day: string;
  totals: Totals;
}

export interface ExerciseHistory {
  exercise: Exercise;
  days: DailyTotalItem[];
  current_streak: number;
  best_day: { day: string; totals: Totals } | null;
  all_time_total: Totals;
  today_total: Totals;
  last_7_days_total: Totals;
  last_30_days_total: Totals;
  recent_logs: ExerciseLog[];
}

export interface CreateExerciseRequest {
  slug: string;
  name: string;
  metric_type: MetricType;
  sort_order: number;
}

export interface UpdateExerciseRequest {
  name: string;
  metric_type: MetricType;
  sort_order: number;
}

export interface ReorderExercisesRequest {
  items: { id: number; sort_order: number }[];
}
