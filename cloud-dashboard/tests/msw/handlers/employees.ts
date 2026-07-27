import { http, HttpResponse } from 'msw';

export const employeeHandlers = [
  http.get('/employees', ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('query')?.toLowerCase();
    const department = url.searchParams.get('department')?.toLowerCase();
    const active = url.searchParams.get('active');

    let employees = [
      {
        id: 'emp-1',
        full_name: 'Alice Dubois',
        employee_number: 'E001',
        department: 'Engineering',
        active: true,
        has_face_reference: true,
        synced_at: '2026-07-27T10:00:00Z',
      },
      {
        id: 'emp-2',
        full_name: 'Bob Martin',
        employee_number: 'E002',
        department: 'Sales',
        active: true,
        has_face_reference: false,
        synced_at: '2026-07-27T10:00:00Z',
      },
      {
        id: 'emp-3',
        full_name: 'Charlie Dupont',
        employee_number: 'E003',
        department: 'Engineering',
        active: false,
        has_face_reference: true,
        synced_at: '2026-07-27T10:00:00Z',
      }
    ];

    if (query) {
      employees = employees.filter(e => 
        e.full_name.toLowerCase().includes(query) || 
        e.employee_number.toLowerCase().includes(query)
      );
    }

    if (department) {
      employees = employees.filter(e => e.department?.toLowerCase() === department);
    }

    if (active === 'true') {
      employees = employees.filter(e => e.active);
    } else if (active === 'false') {
      employees = employees.filter(e => !e.active);
    }

    return HttpResponse.json(employees);
  })
];
