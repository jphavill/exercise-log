import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { provideIcons } from '@ng-icons/core';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';
import { appIcons } from './app/core/icons/app-icons';

bootstrapApplication(AppComponent, {
  providers: [provideHttpClient(), provideRouter(routes), provideIcons(appIcons)],
}).catch((err) => console.error(err));
