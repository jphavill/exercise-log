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
  templateUrl: './exercise-detail.component.html',
  styleUrl: './exercise-detail.component.css',
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
