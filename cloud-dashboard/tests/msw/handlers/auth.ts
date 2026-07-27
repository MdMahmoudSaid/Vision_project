import { http, HttpResponse } from 'msw';

export const authHandlers = [
  http.post('/auth/login', async ({ request }) => {
    const body = await request.json() as any;
    
    if (body.email === 'owner@example.com' && body.password === 'ownerpass') {
      return HttpResponse.json({
        access_token: 'fake-jwt-token-owner',
        token_type: 'bearer',
        user: {
          id: 'user-1',
          email: 'owner@example.com',
          role: 'owner',
          active: true
        }
      });
    }

    if (body.email === 'admin@example.com' && body.password === 'adminpass') {
      return HttpResponse.json({
        access_token: 'fake-jwt-token-admin',
        token_type: 'bearer',
        user: {
          id: 'user-2',
          email: 'admin@example.com',
          role: 'admin',
          active: true
        }
      });
    }

    if (body.email === 'viewer@example.com' && body.password === 'viewerpass') {
      return HttpResponse.json({
        access_token: 'fake-jwt-token-viewer',
        token_type: 'bearer',
        user: {
          id: 'user-3',
          email: 'viewer@example.com',
          role: 'viewer',
          active: true
        }
      });
    }

    return HttpResponse.json(
      { error: 'invalid_credentials', message: 'Invalid credentials or inactive account' },
      { status: 401 }
    );
  })
];
