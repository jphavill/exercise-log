import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, HostListener, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';
import { ActivatedRoute } from '@angular/router';
import * as echarts from 'echarts';
import { EChartsOption, SeriesOption } from 'echarts';

import { ExerciseHistory, ExerciseLog, Totals } from '../../models/api.models';
import { ApiService } from '../../services/api/api.service';
import { formatMetric } from '../../shared/value-format';

@Component({
  selector: 'app-exercise-detail',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  templateUrl: './exercise-detail.component.html',
  styleUrl: './exercise-detail.component.css',
})
export class ExerciseDetailComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('dailyChart') dailyChartRef?: ElementRef<HTMLDivElement>;

  history: ExerciseHistory | null = null;
  showSmoothedTrend = false;
  private dailyChart: echarts.ECharts | null = null;
  private renderQueued = false;

  constructor(
    private readonly api: ApiService,
    private readonly route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const slug = this.route.snapshot.paramMap.get('slug') ?? '';
    this.api.getExerciseHistory(slug, 30).subscribe((history) => {
      this.history = history;
      this.requestChartRender();
    });
  }

  ngAfterViewInit(): void {
    this.requestChartRender();
  }

  ngOnDestroy(): void {
    this.dailyChart?.dispose();
    this.dailyChart = null;
  }

  formatTotals(totals: Totals): string {
    if (!this.history) {
      return '0';
    }
    return formatMetric(this.history.exercise.metric_type, totals.reps, totals.duration_seconds);
  }

  toggleSmoothedTrend(): void {
    this.showSmoothedTrend = !this.showSmoothedTrend;
    this.requestChartRender();
  }

  formatLog(log: ExerciseLog): string {
    return formatMetric(log.metric_type, log.reps, log.duration_seconds, log.weight_lbs);
  }

  @HostListener('window:resize')
  onWindowResize(): void {
    this.dailyChart?.resize();
  }

  private initializeChart(): void {
    if (this.dailyChart || !this.dailyChartRef?.nativeElement) {
      return;
    }
    this.dailyChart = echarts.init(this.dailyChartRef.nativeElement);
  }

  private requestChartRender(): void {
    if (this.renderQueued) {
      return;
    }
    this.renderQueued = true;
    setTimeout(() => {
      this.renderQueued = false;
      this.renderChart();
    });
  }

  private renderChart(): void {
    if (!this.history) {
      return;
    }
    this.initializeChart();
    if (!this.dailyChart) {
      return;
    }

    const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--color-accent').trim() || '#0f766e';
    const axisColor = getComputedStyle(document.documentElement).getPropertyValue('--color-border').trim() || '#d6d3d1';
    const labels = this.history.days.map((item) => this.formatDayLabel(item.day));
    const values = this.history.days.map((item) => item.goal_progress_value);
    const goalValue = this.goalValue();
    const goalLabel = this.goalLabel(goalValue);
    const series: SeriesOption[] = [
      {
        id: 'daily-total',
        name: this.history.exercise.metric_type === 'reps_plus_weight_lbs' ? 'Daily qualifying total' : 'Daily total',
        type: 'line',
        data: values,
        showSymbol: false,
        smooth: false,
        lineStyle: {
          width: 3,
          color: accentColor,
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: accentColor,
            borderColor: '#ffffff',
            borderWidth: 1,
          },
        },
      },
    ];

    if (this.showSmoothedTrend) {
      series.push({
        id: 'smoothed-trend',
        name: 'Smoothed trend',
        type: 'line',
        data: values,
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: accentColor,
          opacity: 0.45,
        },
        tooltip: {
          show: false,
        },
      });
    }

    if (goalValue != null) {
      series.push({
        id: 'goal-line',
        name: 'Goal',
        type: 'line',
        data: labels.map(() => goalValue),
        showSymbol: false,
        smooth: false,
        lineStyle: {
          width: 2,
          type: 'dotted',
          color: accentColor,
          opacity: 0.7,
        },
      });
    }

    const options: EChartsOption = {
      animationDuration: 350,
      grid: {
        left: 40,
        right: 20,
        top: 16,
        bottom: 28,
      },
      xAxis: {
        type: 'category',
        data: labels,
        boundaryGap: false,
        axisLine: { lineStyle: { color: axisColor } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: axisColor,
          },
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'line',
        },
        formatter: (params) => {
          const points = Array.isArray(params) ? params : [params];
          const dateLabel = String((points[0] as { axisValue?: string | number } | undefined)?.axisValue ?? '');
          const lines = [dateLabel];
          for (const point of points) {
            if (point.seriesId === 'goal-line') {
              lines.push(`Goal: ${goalLabel}`);
              continue;
            }
            if (typeof point.value === 'number') {
              lines.push(`${point.seriesName}: ${this.formatMetricValue(point.value)}`);
            }
          }
          return lines.join('<br/>');
        },
      },
      series,
    };

    this.dailyChart.setOption(options, true);
    this.dailyChart.resize();
  }

  private formatDayLabel(day: string): string {
    const parts = day.split('-');
    if (parts.length !== 3) {
      return day;
    }
    return `${Number(parts[1])}/${Number(parts[2])}`;
  }

  private goalValue(): number | null {
    if (!this.history) {
      return null;
    }
    if (this.history.exercise.metric_type === 'duration_seconds') {
      return this.history.exercise.goal_duration_seconds;
    }
    return this.history.exercise.goal_reps;
  }

  private goalLabel(goalValue: number | null): string {
    if (!this.history || goalValue == null) {
      return 'No goal';
    }
    if (this.history.exercise.metric_type === 'duration_seconds') {
      return `${goalValue} seconds`;
    }
    if (this.history.exercise.metric_type === 'reps_plus_weight_lbs') {
      const weight = this.history.exercise.goal_weight_lbs ?? 0;
      return `${goalValue} reps @ ${weight} lbs`;
    }
    return `${goalValue} reps`;
  }

  private formatMetricValue(value: number): string {
    if (!this.history) {
      return String(value);
    }
    if (this.history.exercise.metric_type === 'duration_seconds') {
      return `${value} seconds`;
    }
    if (this.history.exercise.metric_type === 'reps_plus_weight_lbs') {
      const weight = this.history.exercise.goal_weight_lbs ?? 0;
      return `${value} reps @ >= ${weight} lbs`;
    }
    return `${value} reps`;
  }
}
