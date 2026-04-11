import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';

import { ExerciseLog } from '../../../../models/api.models';
import { formatMetric } from '../../../../shared/value-format';

@Component({
  selector: 'app-recent-activity-section',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  templateUrl: './recent-activity-section.component.html',
  styleUrl: './recent-activity-section.component.css',
})
export class RecentActivitySectionComponent {
  readonly initialVisibleCount = 10;
  readonly visibleStep = 10;

  private _recent: ExerciseLog[] = [];
  /**
   * Keeps the current expanded amount across incoming data updates when possible.
   * - First non-empty load starts at the initial visible count.
   * - If the list grows, the existing visible count is preserved.
   * - If the list shrinks, the visible count is clamped to the new length.
   * - Empty -> non-empty initializes again to the initial visible count.
   */
  @Input() set recent(value: ExerciseLog[]) {
    const nextRecent = value ?? [];
    const hadItems = this._recent.length > 0;
    this._recent = nextRecent;
    const minimumVisible = Math.min(this.initialVisibleCount, this._recent.length);

    if (!hadItems && this._recent.length > 0) {
      this.visibleCount = minimumVisible;
      return;
    }
    if (this.visibleCount < minimumVisible) {
      this.visibleCount = minimumVisible;
    }
    if (this.visibleCount > this._recent.length) {
      this.visibleCount = this._recent.length;
    }
  }
  get recent(): ExerciseLog[] {
    return this._recent;
  }

  @Input() openMenuLogId: number | null = null;
  @Output() toggleMenuLog = new EventEmitter<number>();
  @Output() deleteLogClick = new EventEmitter<number>();

  visibleCount = 0;

  get visibleRecent(): ExerciseLog[] {
    return this.recent.slice(0, this.visibleCount);
  }

  get hasMore(): boolean {
    return this.recent.length > this.visibleCount;
  }

  get canCollapse(): boolean {
    return this.visibleCount > this.initialVisibleCount && this.recent.length > this.initialVisibleCount;
  }

  get nextBatchCount(): number {
    return Math.min(this.visibleStep, this.recent.length - this.visibleCount);
  }

  get controls(): { showMore: boolean; showLess: boolean; nextBatchCount: number } {
    return {
      showMore: this.hasMore,
      showLess: this.canCollapse,
      nextBatchCount: this.nextBatchCount,
    };
  }

  formatRecent(log: ExerciseLog): string {
    return formatMetric(log.metric_type, log.reps, log.duration_seconds, log.weight_lbs);
  }

  onToggleClick(logId: number, event: MouseEvent): void {
    event.stopPropagation();
    this.toggleMenuLog.emit(logId);
  }

  onMenuClick(event: MouseEvent): void {
    event.stopPropagation();
  }

  onDeleteClick(logId: number, event: MouseEvent): void {
    event.stopPropagation();
    this.deleteLogClick.emit(logId);
  }

  showMore(): void {
    this.visibleCount = Math.min(this.visibleCount + this.visibleStep, this.recent.length);
  }

  showLess(): void {
    this.visibleCount = Math.min(this.initialVisibleCount, this.recent.length);
  }

  trackByLogId(_: number, log: ExerciseLog): number {
    return log.id;
  }
}
