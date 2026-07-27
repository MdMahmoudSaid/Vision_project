import { setupServer } from 'msw/node';
import { authHandlers } from './handlers/auth';
import { employeeHandlers } from './handlers/employees';
import { reportHandlers } from './handlers/reports';
import { correctionHandlers } from './handlers/corrections';
import { userHandlers } from './handlers/users';

export const server = setupServer(
  ...authHandlers,
  ...employeeHandlers,
  ...reportHandlers,
  ...correctionHandlers,
  ...userHandlers
);
