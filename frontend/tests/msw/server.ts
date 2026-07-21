import { setupServer } from 'msw/node';
import { authHandlers } from './handlers/auth';
import { employeeHandlers } from './handlers/employees';
import { attendanceHandlers } from './handlers/attendance';
import { employeeManagementHandlers } from './handlers/employeeManagement';

export const server = setupServer(...authHandlers, ...employeeHandlers, ...attendanceHandlers, ...employeeManagementHandlers);
