import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';
import { ActivatedRoute } from '@angular/router';

import { DailyTotalItem, ExerciseHistory, ExerciseLog, Totals } from '../../models/api.models';
import { ApiService } from '../../services/api/api.service';
import { formatMetric } from '../../shared/value-format';

@Component({
  selector: 'app-exercise-detail',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  template: `
    <section *ngIf="history; else loading">
      <h2 class="section-title"><ng-icon name="navExercises" aria-hidden="true"></ng-icon><span>{{ history.exercise.name }}</span></h2>
      <div class="card-grid">
        <div class="card card-inline"><ng-icon name="sectionToday" aria-hidden="true"></ng-icon><span>Today: {{ formatTotals(history.today_total) }}</span></div>
        <div class="card card-inline"><ng-icon name="sectionWeek" aria-hidden="true"></ng-icon><span>7 days: {{ formatTotals(history.last_7_days_total) }}</span></div>
        <div class="card card-inline"><ng-icon name="sectionTrends" aria-hidden="true"></ng-icon><span>30 days: {{ formatTotals(history.last_30_days_total) }}</span></div>
        <div class="card card-inline"><ng-icon name="sectionRecent" aria-hidden="true"></ng-icon><span>All-time: {{ formatTotals(history.all_time_total) }}</span></div>
      </div>
      <p class="meta-inline"><ng-icon name="sectionTrends" aria-hidden="true"></ng-icon><span>Current streak: {{ history.current_streak }} days</span></p>
      <p *ngIf="history.best_day">Best day: {{ history.best_day.day }} ({{ formatTotals(history.best_day.totals) }})</p>

      <h3 class="section-title"><ng-icon name="sectionTrends" aria-hidden="true"></ng-icon><span>Daily totals</span></h3>
      <div class="trend-list" *ngFor="let item of history.days">
        <div class="trend-label">{{ item.day }}</div>
        <div class="trend-bar-wrap">
          <div class="trend-bar" [style.width.%]="barPercent(item)"></div>
        </div>
      </div>

      <h3 class="section-title"><ng-icon name="sectionRecent" aria-hidden="true"></ng-icon><span>Recent entries</span></h3>
      <div class="feed-item" *ngFor="let log of history.recent_logs">
        {{ formatLog(log) }} - {{ log.logged_at | date: 'short' }}
      </div>
    </section>
    <ng-template #loading><p>Loading...</p></ng-template>
  `,
})
export class ExerciseDetailComponent implements OnInit {
  history: ExerciseHistory | null = null;

  constructor(
    private readonly api: ApiService,
    private readonly route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const slug = this.route.snapshot.paramMap.get('slug') ?? '';
    this.api.getExerciseHistory(slug, 30).subscribe((history) => (this.history = history));
  }

  formatTotals(totals: Totals): string {
    if (!this.history) {
      return '0';
    }
    return formatMetric(this.history.exercise.metric_type, totals.reps, totals.duration_seconds);
  }

  barPercent(item: DailyTotalItem): number {
    if (!this.history) {
      return 0;
    }
    const raw =
      this.history.exercise.metric_type === 'duration_seconds'
        ? item.totals.duration_seconds
        : item.totals.reps;
    return Math.max(3, Math.min(100, (raw ?? 0) * 4));
  }

  formatLog(log: ExerciseLog): string {
    return formatMetric(log.metric_type, log.reps, log.duration_seconds, log.weight_lbs);
  }
}
