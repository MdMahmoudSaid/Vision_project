import { http, HttpResponse } from 'msw';

let correctionsStore: any[] = [];

export function resetCorrectionsStore() {
  correctionsStore = [];
}

export const correctionHandlers = [
  http.get('/employees/:id/attendance', ({ params }) => {
    return HttpResponse.json({
      employee_id: params.id,
      employee_name: 'Alice Dubois',
      may_be_incomplete: false,
      days: [
        {
          employee_id: params.id,
          employee_name: 'Alice Dubois',
          date: '2026-07-27',
          arrival_time: '2026-07-27T08:00:00Z',
          departure_time: null,
          worked_duration_minutes: null,
          completeness: 'missing_departure',
          corrected: false,
        },
      ],
    });
  }),

  http.get('/attendance/corrections/:id', () => {
    return HttpResponse.json(correctionsStore);
  }),

  http.post('/attendance/corrections', async ({ request }) => {
    const body = (await request.json()) as any;

    if (!body.reason || !body.reason.trim()) {
      return HttpResponse.json(
        { error: 'invalid_reason', message: 'Reason must not be empty' },
        { status: 400 }
      );
    }

    const correction = {
      id: `correction-${correctionsStore.length + 1}`,
      employee_id: body.employee_id,
      attendance_event_id: body.attendance_event_id ?? null,
      action: body.action,
      previous_value: null,
      new_value: body.new_value,
      reason: body.reason,
      performed_by: 'admin-1',
      performed_at: new Date().toISOString(),
    };
    correctionsStore.push(correction);

    return HttpResponse.json(correction, { status: 201 });
  }),
];
