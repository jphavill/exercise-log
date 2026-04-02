import { Component } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgIconComponent],
  template: `
    <div class="shell">
      <header class="topbar">
        <h1>NFC Exercise Tracker</h1>
        <nav>
          <a class="nav-link" routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">
            <ng-icon name="navDashboard" aria-hidden="true"></ng-icon>
            <span>Dashboard</span>
          </a>
          <a class="nav-link" routerLink="/exercises" routerLinkActive="active">
            <ng-icon name="navExercises" aria-hidden="true"></ng-icon>
            <span>Exercises</span>
          </a>
        </nav>
      </header>
      <main>
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
})
export class AppComponent {}
