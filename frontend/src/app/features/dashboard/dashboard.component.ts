import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../services/api/api.service';
import { ConsistencyDayItem, DashboardSummary, ExerciseConsistencyItem, ExerciseLog, MetricType } from '../../models/api.models';
import { formatMetric } from '../../shared/value-format';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIconComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  summary: DashboardSummary | null = null;
  recent: ExerciseLog[] = [];
  openMenuLogId: number | null = null;
  readonly intensityLegend = [
    { className: 'level-0', label: 'None' },
    { className: 'level-1', label: 'Light' },
    { className: 'level-2', label: 'Medium' },
    { className: 'level-3', label: 'High' },
    { className: 'level-4', label: 'Peak' },
  ];

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboardSummary().subscribe((summary) => (this.summary = summary));
    this.loadRecentLogs();
  }

  @HostListener('document:click')
  onDocumentClick(): void {
    this.openMenuLogId = null;
  }

  toggleMenu(logId: number, event: MouseEvent): void {
    event.stopPropagation();
    this.openMenuLogId = this.openMenuLogId === logId ? null : logId;
  }

  onMenuClick(event: MouseEvent): void {
    event.stopPropagation();
  }

  deleteLog(logId: number): void {
    this.openMenuLogId = null;
    this.api.deleteLog(logId).subscribe({
      next: () => {
        this.recent = this.recent.filter((log) => log.id !== logId);
      },
    });
  }

  metricValue(metricType: MetricType, reps: number | null, durationSeconds: number | null): string {
    return formatMetric(metricType, reps, durationSeconds);
  }

  formatRecent(log: ExerciseLog): string {
    return formatMetric(log.metric_type, log.reps, log.duration_seconds, log.weight_lbs);
  }

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

  scalingModeDescription(row: ExerciseConsistencyItem): string {
    if (row.scaling_mode === 'goal' && row.goal_target_value) {
      return `Goal: ${row.goal_target_value}`;
    }
    return 'Relative: peak in last 30 days';
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

  private loadRecentLogs(): void {
    this.api.getRecentLogs(20).subscribe((logs) => (this.recent = logs));
  }

  private metricTotalValue(row: ExerciseConsistencyItem): number {
    return row.metric_type === 'duration_seconds' ? (row.window_totals.duration_seconds ?? 0) : (row.window_totals.reps ?? 0);
  }

}
