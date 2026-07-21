import { http, HttpResponse } from 'msw';

export const employeeHandlers = [
  http.get('/employees', ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('query');
    
    if (query === 'Ahmed') {
      return HttpResponse.json([
        {
          id: '223e4567-e89b-12d3-a456-426614174001',
          full_name: 'Ahmed Mohamed',
          employee_number: 'EMP-001',
          department: 'Security',
          active: true,
          has_face_reference: true
        }
      ]);
    }

    return HttpResponse.json([]);
  })
];
