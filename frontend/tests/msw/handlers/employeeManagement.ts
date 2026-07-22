import { http, HttpResponse } from 'msw';

export const employeeManagementHandlers = [
  http.post('/employees', async ({ request }) => {
    const body = (await request.json()) as any;

    if (body.employee_number === 'FORBIDDEN') {
      return HttpResponse.json({ error: 'forbidden', message: 'Admin role required' }, { status: 403 });
    }

    return HttpResponse.json(
      {
        id: 'new-emp-123',
        full_name: body.full_name,
        employee_number: body.employee_number || 'EMP0002',
        department: body.department ?? null,
        active: true,
        has_face_reference: false,
        job_title: null,
        phone: null,
        notes: null,
        registration_date: '2026-07-20',
        created_at: '2026-07-20T12:23:26.401Z',
        updated_at: '2026-07-20T12:23:26.401Z'
      },
      { status: 201 }
    );
  }),

  http.post('/employees/:employee_id/face', async ({ params }) => {
    if (params.employee_id === 'no-face-emp-id') {
      return HttpResponse.json(
        {
          error: 'no_face_detected',
          message: "Could not get a clear view of the employee's face."
        },
        { status: 400 }
      );
    }
    return HttpResponse.json({
      employee_id: params.employee_id as string,
      status: 'usable',
      sample_count: 3,
      enrolled_at: '2026-07-20T14:35:10.009Z'
    });
  }),

  http.delete('/employees/:employee_id', ({ params, request }) => {
    const url = new URL(request.url);
    const force = url.searchParams.get('force') === 'true';

    if (params.employee_id === 'has-history-id' && !force) {
      return HttpResponse.json(
        {
          error: 'employee_has_history',
          message: 'This employee has attendance history and cannot be deleted. Deactivate them instead.'
        },
        { status: 409 }
      );
    }
    if (params.employee_id === 'not-found-id') {
      return HttpResponse.json({ error: 'employee_not_found', message: 'Employee not found' }, { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),

  http.patch('/employees/:employee_id', async ({ params, request }) => {
    const body = (await request.json()) as any;
    return HttpResponse.json({
      id: params.employee_id as string,
      full_name: 'Deactivated Employee',
      employee_number: 'EMP-DEACT',
      department: null,
      active: body.active ?? false,
      has_face_reference: false,
      job_title: null,
      phone: null,
      notes: null,
      registration_date: '2026-07-20',
      created_at: '2026-07-20T12:23:26.401Z',
      updated_at: '2026-07-20T12:23:26.401Z'
    });
  })
];
