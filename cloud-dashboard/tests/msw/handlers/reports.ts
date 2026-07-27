import { http, HttpResponse } from 'msw';

export const reportHandlers = [
  http.get('/reports/daily', ({ request }) => {
    const url = new URL(request.url);
    const date = url.searchParams.get('date');

    return HttpResponse.json({
      scope: { type: 'organization' },
      period: { granularity: 'day', date_from: date, date_to: date },
      rows: [
        {
          employee_id: 'emp-1',
          employee_name: 'Alice Dubois',
          date: date,
          arrival_time: `${date}T08:00:00Z`,
          departure_time: `${date}T17:00:00Z`,
          worked_duration_minutes: 540,
          completeness: 'complete',
          corrected: false
        }
      ],
      generated_at: new Date().toISOString(),
      may_be_incomplete: false
    });
  }),

  http.get('/reports/weekly', ({ request }) => {
    const url = new URL(request.url);
    const weekStart = url.searchParams.get('week_start');

    return HttpResponse.json({
      scope: { type: 'organization' },
      period: { granularity: 'week', date_from: weekStart, date_to: weekStart },
      rows: [],
      generated_at: new Date().toISOString(),
      may_be_incomplete: false
    });
  }),

  http.get('/reports/monthly', ({ request }) => {
    const url = new URL(request.url);
    const month = url.searchParams.get('month');

    return HttpResponse.json({
      scope: { type: 'organization' },
      period: { granularity: 'month', date_from: `${month}-01`, date_to: `${month}-30` },
      rows: [],
      generated_at: new Date().toISOString(),
      may_be_incomplete: false
    });
  }),

  http.get('/reports/custom', ({ request }) => {
    const url = new URL(request.url);
    const dateFrom = url.searchParams.get('date_from');
    const dateTo = url.searchParams.get('date_to');

    return HttpResponse.json({
      scope: { type: 'organization' },
      period: { granularity: 'custom', date_from: dateFrom, date_to: dateTo },
      rows: [],
      generated_at: new Date().toISOString(),
      may_be_incomplete: false
    });
  }),

  http.get('/reports/export', ({ request }) => {
    const url = new URL(request.url);
    const format = url.searchParams.get('format');

    if (format === 'pdf') {
      return new HttpResponse(new Blob(['%PDF-mock-data'], { type: 'application/pdf' }));
    } else {
      return new HttpResponse(new Blob(['mock-excel-data'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
    }
  })
];
