import { Component } from '@angular/core';
import { NgIconComponent } from '@ng-icons/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgIconComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  constructor(private readonly router: Router) {}

  isWorkoutPlayer(): boolean {
    return /^\/workouts\/[^/?#]+/.test(this.router.url);
  }
}
