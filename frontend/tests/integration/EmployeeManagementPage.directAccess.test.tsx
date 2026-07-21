import { describe, it, expect } from 'vitest';
import { createEmployee } from '../../src/api/employees';
import { server } from '../msw/server';
import { http, HttpResponse } from 'msw';

describe('EmployeeManagement API Direct Access', () => {
  it('rejects API call if user is not authorized', async () => {
    server.use(
      http.post('/employees', () => {
        return HttpResponse.json({ detail: 'Forbidden' }, { status: 403 });
      })
    );
    
    await expect(createEmployee({
      full_name: 'Test',
      employee_number: 'EMP-999',
      department: null
    })).rejects.toThrow();
  });
});
