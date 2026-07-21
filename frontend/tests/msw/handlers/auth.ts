import { http, HttpResponse } from 'msw';

export const authHandlers = [
  http.post('/auth/login', async ({ request }) => {
    const body = (await request.json()) as any;
    
    if (body.username === 'garde1' && body.password === 'my_password') {
      return HttpResponse.json({
        access_token: 'fake_token',
        token_type: 'bearer',
        user: {
          id: 'user-id',
          username: 'garde1',
          full_name: 'Ahmed Guard',
          role: 'guard'
        }
      });
    }

    return HttpResponse.json({ detail: 'Incorrect username or password' }, { status: 401 });
  })
];
