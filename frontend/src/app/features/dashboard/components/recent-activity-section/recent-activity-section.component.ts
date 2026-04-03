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
  @Input() recent: ExerciseLog[] = [];
  @Input() openMenuLogId: number | null = null;
  @Output() toggleMenuLog = new EventEmitter<number>();
  @Output() deleteLogClick = new EventEmitter<number>();

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
}
