import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';

import { ApiService } from '../../services/api/api.service';
import { DashboardSummary, ExerciseLog } from '../../models/api.models';
import { ConsistencySectionComponent } from './components/consistency-section/consistency-section.component';
import { RecentActivitySectionComponent } from './components/recent-activity-section/recent-activity-section.component';
import { TodayWeekSectionComponent } from './components/today-week-section/today-week-section.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, TodayWeekSectionComponent, ConsistencySectionComponent, RecentActivitySectionComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  summary: DashboardSummary | null = null;
  recent: ExerciseLog[] = [];
  openMenuLogId: number | null = null;

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    this.api.getDashboardSummary().subscribe((summary) => (this.summary = summary));
    this.loadRecentLogs();
  }

  @HostListener('document:click')
  onDocumentClick(): void {
    this.openMenuLogId = null;
  }

  toggleMenu(logId: number): void {
    this.openMenuLogId = this.openMenuLogId === logId ? null : logId;
  }

  deleteLog(logId: number): void {
    this.openMenuLogId = null;
    this.api.deleteLog(logId).subscribe({
      next: () => {
        this.recent = this.recent.filter((log) => log.id !== logId);
      },
    });
  }

  private loadRecentLogs(): void {
    this.api.getRecentLogs(20).subscribe((logs) => (this.recent = logs));
  }
}
