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
  template: `
    <section class="section">
      <h2 class="section-title"><ng-icon name="sectionToday" aria-hidden="true"></ng-icon><span>Today</span></h2>
      <div class="card-grid" *ngIf="summary">
        <a class="card" *ngFor="let item of summary.today" [routerLink]="['/exercise', item.exercise_slug]">
          <strong>{{ item.exercise_name }}</strong>
          <span>{{ metricValue(item.metric_type, item.totals.reps, item.totals.duration_seconds) }}</span>
        </a>
      </div>
    </section>

    <section class="section" *ngIf="summary">
      <h2 class="section-title"><ng-icon name="sectionWeek" aria-hidden="true"></ng-icon><span>This Week</span></h2>
      <div class="card-grid">
        <div class="card" *ngFor="let item of summary.current_week">
          <strong>{{ item.exercise_name }}</strong>
          <span>{{ metricValue(item.metric_type, item.totals.reps, item.totals.duration_seconds) }}</span>
        </div>
      </div>
    </section>

    <section class="section" *ngIf="summary">
      <h2 class="section-title"><ng-icon name="sectionTrends" aria-hidden="true"></ng-icon><span>Quick Trends (30 Days)</span></h2>
      <div class="trend-list" *ngFor="let item of summary.last_30_days">
        <div class="trend-label">{{ item.exercise_name }}</div>
        <div class="trend-bar-wrap">
          <div class="trend-bar" [style.width.%]="barPercent(item)"></div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title"><ng-icon name="sectionRecent" aria-hidden="true"></ng-icon><span>Recent Activity</span></h2>
      <div class="feed" *ngIf="recent.length; else emptyLogs">
        <div class="feed-item" *ngFor="let log of recent">
          <span>
            {{ log.exercise_name }} -
            {{ formatRecent(log) }} -
            {{ log.logged_at | date: 'shortTime' }}
          </span>
        </div>
      </div>
      <ng-template #emptyLogs><p>No logs yet.</p></ng-template>
    </section>
  `,
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
