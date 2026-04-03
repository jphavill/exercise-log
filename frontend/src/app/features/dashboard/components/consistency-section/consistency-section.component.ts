import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';

import { ConsistencyDayItem, DashboardSummary, ExerciseConsistencyItem } from '../../../../models/api.models';
import { formatMetric } from '../../../../shared/value-format';

@Component({
  selector: 'app-consistency-section',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  templateUrl: './consistency-section.component.html',
  styleUrl: './consistency-section.component.css',
})
export class ConsistencySectionComponent {
  @Input() summary: DashboardSummary | null = null;

  topConsistencyRows(): ExerciseConsistencyItem[] {
    if (!this.summary) {
      return [];
    }

    return [...this.summary.last_30_days_consistency]
      .sort((a, b) => {
        if (b.active_days !== a.active_days) {
          return b.active_days - a.active_days;
        }
        if (b.total_logs !== a.total_logs) {
          return b.total_logs - a.total_logs;
        }
        return this.metricTotalValue(b) - this.metricTotalValue(a);
      })
      .slice(0, 6);
  }

  heatLevelClass(_row: ExerciseConsistencyItem, day: ConsistencyDayItem): string {
    return `level-${day.intensity_level}`;
  }

  heatCellTitle(row: ExerciseConsistencyItem, day: ConsistencyDayItem): string {
    const reps = day.totals.reps ?? 0;
    const duration = day.totals.duration_seconds ?? 0;

    if (row.metric_type === 'duration_seconds') {
      return `${duration} sec`;
    }

    if (row.metric_type === 'reps_plus_weight_lbs' && row.scaling_mode === 'goal' && row.goal_weight_lbs) {
      return `${reps} reps (${day.progress_value} reps at >= ${row.goal_weight_lbs} lbs)`;
    }

    return `${reps} reps`;
  }

  trackByDay(_index: number, day: ConsistencyDayItem): string {
    return day.day;
  }

  metricTotal(row: ExerciseConsistencyItem): string {
    return formatMetric(row.metric_type, row.window_totals.reps, row.window_totals.duration_seconds);
  }

  private metricTotalValue(row: ExerciseConsistencyItem): number {
    return row.metric_type === 'duration_seconds' ? (row.window_totals.duration_seconds ?? 0) : (row.window_totals.reps ?? 0);
  }
}
