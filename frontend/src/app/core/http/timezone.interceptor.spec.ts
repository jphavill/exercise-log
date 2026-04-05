import { describe, expect, it, vi } from 'vitest';
import { HttpHeaders, HttpRequest, HttpResponse } from '@angular/common/http';
import { of } from 'rxjs';

import { timezoneInterceptor } from './timezone.interceptor';

describe('timezoneInterceptor', () => {
  it('adds X-Timezone header when browser timezone is present', () => {
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: 'America/New_York' }),
    } as Intl.DateTimeFormat);

    const req = new HttpRequest('GET', '/api/dashboard/summary');
    const next = vi.fn((request: HttpRequest<unknown>) => of(new HttpResponse({ status: request.headers.has('X-Timezone') ? 200 : 500 })));

    timezoneInterceptor(req, next).subscribe();

    expect(next).toHaveBeenCalledOnce();
    const forwardedRequest = next.mock.calls[0][0] as HttpRequest<unknown>;
    expect(forwardedRequest.headers.get('X-Timezone')).toBe('America/New_York');
    expect(req.headers.has('X-Timezone')).toBe(false);
  });

  it('does not add header when browser timezone is missing', () => {
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: '' }),
    } as Intl.DateTimeFormat);

    const req = new HttpRequest('GET', '/api/dashboard/summary');
    const next = vi.fn((request: HttpRequest<unknown>) => of(new HttpResponse({ status: request.headers.has('X-Timezone') ? 500 : 200 })));

    timezoneInterceptor(req, next).subscribe();

    expect(next).toHaveBeenCalledOnce();
    const forwardedRequest = next.mock.calls[0][0] as HttpRequest<unknown>;
    expect(forwardedRequest.headers.has('X-Timezone')).toBe(false);
  });

  it('overwrites stale X-Timezone header from original request', () => {
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: 'Asia/Tokyo' }),
    } as Intl.DateTimeFormat);

    const req = new HttpRequest('GET', '/api/dashboard/summary', null, {
      headers: new HttpHeaders({ 'X-Timezone': 'UTC' }),
    });
    const next = vi.fn((request: HttpRequest<unknown>) => of(new HttpResponse({ status: 200, body: request.headers.get('X-Timezone') })));

    timezoneInterceptor(req, next).subscribe();

    const forwardedRequest = next.mock.calls[0][0] as HttpRequest<unknown>;
    expect(forwardedRequest.headers.get('X-Timezone')).toBe('Asia/Tokyo');
    expect(req.headers.get('X-Timezone')).toBe('UTC');
  });

  it('passes through request unchanged when resolvedOptions returns undefined timezone', () => {
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: undefined }),
    } as Intl.DateTimeFormat);

    const req = new HttpRequest('POST', '/api/logs', { exercise_slug: 'pullups', reps: 5 });
    const next = vi.fn((request: HttpRequest<unknown>) => of(new HttpResponse({ status: request === req ? 200 : 500 })));

    timezoneInterceptor(req, next).subscribe();

    expect(next).toHaveBeenCalledWith(req);
    expect((next.mock.calls[0][0] as HttpRequest<unknown>).headers.has('X-Timezone')).toBe(false);
  });
});
