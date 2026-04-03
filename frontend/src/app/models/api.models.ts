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
  goal_reps: number | null;
  goal_duration_seconds: number | null;
  goal_weight_lbs: number | null;
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
  last_30_days_consistency: ExerciseConsistencyItem[];
  total_logs_today: number;
  total_logs_this_week: number;
}

export interface ConsistencyDayItem {
  day: string;
  totals: Totals;
  progress_value: number;
  intensity_level: 0 | 1 | 2 | 3 | 4;
}

export interface ExerciseConsistencyItem {
  exercise_id: number;
  exercise_slug: string;
  exercise_name: string;
  metric_type: MetricType;
  window_totals: Totals;
  active_days: number;
  total_logs: number;
  scaling_mode: 'goal' | 'relative';
  goal_target_value: number | null;
  goal_weight_lbs: number | null;
  days: ConsistencyDayItem[];
}

export interface DailyTotalItem {
  day: string;
  totals: Totals;
  goal_progress_value: number;
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
  goal_reps: number | null;
  goal_duration_seconds: number | null;
  goal_weight_lbs: number | null;
}

export interface UpdateExerciseRequest {
  name: string;
  metric_type: MetricType;
  sort_order: number;
  goal_reps: number | null;
  goal_duration_seconds: number | null;
  goal_weight_lbs: number | null;
}

export interface ReorderExercisesRequest {
  items: { id: number; sort_order: number }[];
}
