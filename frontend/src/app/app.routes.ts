import { Routes } from '@angular/router';

import { DashboardComponent } from './features/dashboard/dashboard.component';
import { ExerciseDetailComponent } from './features/exercise-detail/exercise-detail.component';
import { ExerciseManagementComponent } from './features/exercise-management/exercise-management.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'exercise/:slug', component: ExerciseDetailComponent },
  { path: 'exercises', component: ExerciseManagementComponent },
];
