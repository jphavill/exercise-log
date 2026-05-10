import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnDestroy, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { EMPTY, catchError, map, switchMap } from 'rxjs';

import { Workout, WorkoutStep } from '../../models/api.models';
import { ApiService } from '../../services/api/api.service';

type PlayerState = 'loading' | 'ready' | 'intro' | 'active' | 'finished' | 'error';

@Component({
  selector: 'app-workout-player',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './workout-player.component.html',
  styleUrl: './workout-player.component.css',
})
export class WorkoutPlayerComponent implements OnInit, OnDestroy {
  workout: Workout | null = null;
  state: PlayerState = 'loading';
  countdown: number | null = null;
  currentStepIndex = 0;

  private readonly api = inject(ApiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private intervalId: number | null = null;
  private readyTimeoutId: number | null = null;

  ngOnInit(): void {
    this.route.paramMap
      .pipe(
        map((params) => Number(params.get('id'))),
        switchMap((id) => {
          this.resetPlayer('loading');

          if (!Number.isInteger(id) || id <= 0) {
            this.state = 'error';
            return EMPTY;
          }

          return this.api.getWorkout(id).pipe(
            catchError(() => {
              this.resetPlayer('error');
              return EMPTY;
            }),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((workout) => {
        this.workout = workout;
        this.state = 'ready';
        this.currentStepIndex = 0;
        this.readyTimeoutId = window.setTimeout(() => this.startIntroCountdown(), 750);
      });
  }

  ngOnDestroy(): void {
    this.clearTimers();
  }

  get title(): string {
    return this.workout?.name ?? 'Workout';
  }

  get currentStep(): WorkoutStep | null {
    if (!this.workout || this.state === 'finished' || this.state === 'ready') {
      return null;
    }

    return this.workout.steps[this.currentStepIndex] ?? null;
  }

  get nextStep(): WorkoutStep | null {
    if (!this.workout || this.state === 'finished' || this.state === 'ready') {
      return null;
    }

    return this.workout.steps[this.currentStepIndex + 1] ?? null;
  }

  get showCountdown(): boolean {
    return this.state === 'intro' || (this.state === 'active' && this.currentStep !== null && this.isTimedStep(this.currentStep));
  }

  get showDoneButton(): boolean {
    return this.state === 'active' && this.currentStep !== null && !this.isTimedStep(this.currentStep);
  }

  goBack(): void {
    void this.router.navigate(['/workouts']);
  }

  completeRepStep(): void {
    if (!this.showDoneButton) {
      return;
    }

    this.advanceStep();
  }

  stepMetadata(step: WorkoutStep): string {
    if (this.isTimedStep(step)) {
      return `${step.duration_sec} sec`;
    }

    return `${step.reps} ${step.rep_unit}`;
  }

  isTimedStep(step: WorkoutStep): step is Extract<WorkoutStep, { kind: 'timed_exercise' | 'rest' }> {
    return step.kind === 'timed_exercise' || step.kind === 'rest';
  }

  private startIntroCountdown(): void {
    if (!this.workout) {
      return;
    }

    this.currentStepIndex = 0;
    this.state = 'intro';
    this.startCountdown(3, () => this.startActiveStep());
  }

  private startActiveStep(): void {
    if (!this.workout || this.currentStepIndex >= this.workout.steps.length) {
      this.finishWorkout();
      return;
    }

    this.state = 'active';
    const step = this.workout.steps[this.currentStepIndex];

    if (this.isTimedStep(step)) {
      this.startCountdown(step.duration_sec, () => this.advanceStep());
      return;
    }

    this.countdown = null;
  }

  private advanceStep(): void {
    this.clearInterval();

    if (!this.workout) {
      this.finishWorkout();
      return;
    }

    this.currentStepIndex += 1;
    this.startActiveStep();
  }

  private finishWorkout(): void {
    this.clearTimers();
    this.countdown = null;
    this.state = 'finished';
  }

  private startCountdown(seconds: number, onComplete: () => void): void {
    this.clearInterval();
    this.countdown = seconds;
    this.intervalId = window.setInterval(() => {
      if (this.countdown === null) {
        return;
      }

      if (this.countdown <= 1) {
        this.clearInterval();
        onComplete();
        return;
      }

      this.countdown -= 1;
    }, 1000);
  }

  private resetPlayer(state: PlayerState): void {
    this.clearTimers();
    this.workout = null;
    this.state = state;
    this.countdown = null;
    this.currentStepIndex = 0;
  }

  private clearTimers(): void {
    this.clearInterval();
    if (this.readyTimeoutId !== null) {
      window.clearTimeout(this.readyTimeoutId);
      this.readyTimeoutId = null;
    }
  }

  private clearInterval(): void {
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}
