import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { NgIconComponent } from '@ng-icons/core';

import { Workout } from '../../models/api.models';
import { ApiService } from '../../services/api/api.service';

@Component({
  selector: 'app-workouts',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  templateUrl: './workouts.component.html',
  styleUrl: './workouts.component.css',
})
export class WorkoutsComponent implements OnInit {
  workouts: Workout[] = [];
  hasLoaded = false;

  constructor(
    private readonly api: ApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.api.getWorkouts().subscribe({
      next: (workouts) => {
        this.workouts = workouts;
        this.hasLoaded = true;
      },
      error: () => {
        this.workouts = [];
        this.hasLoaded = true;
      },
    });
  }

  selectWorkout(workout: Workout): void {
    sessionStorage.setItem('selectedWorkout', JSON.stringify(workout));
    void this.router.navigate(['/workouts'], { queryParams: { workoutId: workout.id } });
  }

  trackByWorkoutId(_: number, workout: Workout): number {
    return workout.id;
  }
}
