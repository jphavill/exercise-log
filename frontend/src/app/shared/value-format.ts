import { MetricType } from '../models/api.models';

export function formatMetric(
  metricType: MetricType,
  reps: number | null,
  durationSeconds: number | null,
  weightLbs?: number | null,
): string {
  if (metricType === 'duration_seconds') {
    return `${durationSeconds ?? 0} sec`;
  }
  if (metricType === 'reps_plus_weight_lbs') {
    if (weightLbs != null && reps != null) {
      return `${reps} reps @ ${weightLbs} lbs`;
    }
    return `${reps ?? 0} reps`;
  }
  return `${reps ?? 0} reps`;
}
