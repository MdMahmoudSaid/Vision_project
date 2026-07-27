import { http, HttpResponse } from 'msw';

let usersStore: any[] = [
  { id: 'owner-1', email: 'owner@example.com', role: 'owner', active: true },
  { id: 'admin-1', email: 'admin@example.com', role: 'admin', active: true },
];

export function resetUsersStore() {
  usersStore = [
    { id: 'owner-1', email: 'owner@example.com', role: 'owner', active: true },
    { id: 'admin-1', email: 'admin@example.com', role: 'admin', active: true },
  ];
}

export const userHandlers = [
  http.get('/users', () => {
    return HttpResponse.json(usersStore);
  }),

  http.post('/users', async ({ request }) => {
    const body = (await request.json()) as any;

    if (usersStore.some((u) => u.email === body.email)) {
      return HttpResponse.json(
        { error: 'email_already_exists', message: `A cloud user with email ${body.email} already exists` },
        { status: 409 }
      );
    }

    const user = {
      id: `user-${usersStore.length + 1}`,
      email: body.email,
      role: body.role,
      active: true,
    };
    usersStore.push(user);
    return HttpResponse.json(user, { status: 201 });
  }),

  http.patch('/users/:id', async ({ params, request }) => {
    const body = (await request.json()) as any;
    const user = usersStore.find((u) => u.id === params.id);
    if (!user) {
      return HttpResponse.json({ error: 'user_not_found', message: 'Cloud user not found' }, { status: 404 });
    }
    if (body.role !== undefined) user.role = body.role;
    if (body.active !== undefined) user.active = body.active;
    return HttpResponse.json(user);
  }),
];
