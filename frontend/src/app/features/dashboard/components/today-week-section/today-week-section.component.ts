import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIconComponent } from '@ng-icons/core';

import { DashboardSummary, ExerciseTotalsItem, MetricType, Totals } from '../../../../models/api.models';
import { formatMetric } from '../../../../shared/value-format';

interface DashboardTotalsCard {
  exercise_slug: string;
  exercise_name: string;
  metric_type: MetricType;
  today_totals: Totals;
  week_totals: Totals;
}

@Component({
  selector: 'app-today-week-section',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIconComponent],
  templateUrl: './today-week-section.component.html',
  styleUrl: './today-week-section.component.css',
})
export class TodayWeekSectionComponent {
  @Input() summary: DashboardSummary | null = null;

  metricValue(metricType: MetricType, reps: number | null, durationSeconds: number | null): string {
    return formatMetric(metricType, reps, durationSeconds);
  }

  dashboardCards(): DashboardTotalsCard[] {
    if (!this.summary) {
      return [];
    }

    const cards = new Map<string, DashboardTotalsCard>();

    for (const item of this.summary.current_week) {
      cards.set(item.exercise_slug, {
        exercise_slug: item.exercise_slug,
        exercise_name: item.exercise_name,
        metric_type: item.metric_type,
        today_totals: this.blankTotals(),
        week_totals: item.totals,
      });
    }

    for (const item of this.summary.today) {
      const existing = cards.get(item.exercise_slug);
      if (existing) {
        existing.today_totals = item.totals;
      } else {
        cards.set(item.exercise_slug, this.cardFromTodayOnly(item));
      }
    }

    return Array.from(cards.values());
  }

  private blankTotals(): Totals {
    return { reps: null, duration_seconds: null };
  }

  private cardFromTodayOnly(item: ExerciseTotalsItem): DashboardTotalsCard {
    return {
      exercise_slug: item.exercise_slug,
      exercise_name: item.exercise_name,
      metric_type: item.metric_type,
      today_totals: item.totals,
      week_totals: item.totals,
    };
  }
}
