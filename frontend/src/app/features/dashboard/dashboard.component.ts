import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../services/api/api.service';
import { DashboardSummary, ExerciseLog, ExerciseTotalsItem, MetricType } from '../../models/api.models';
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

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboardSummary().subscribe((summary) => (this.summary = summary));
    this.api.getRecentLogs(20).subscribe((logs) => (this.recent = logs));
  }

  metricValue(metricType: MetricType, reps: number | null, durationSeconds: number | null): string {
    return formatMetric(metricType, reps, durationSeconds);
  }

  formatRecent(log: ExerciseLog): string {
    return formatMetric(log.metric_type, log.reps, log.duration_seconds, log.weight_lbs);
  }

  barPercent(item: ExerciseTotalsItem): number {
    const raw = item.metric_type === 'duration_seconds' ? item.totals.duration_seconds : item.totals.reps;
    return Math.max(5, Math.min(100, (raw ?? 0) * 4));
  }
}
