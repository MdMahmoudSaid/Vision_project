import { apiClient } from './client';
import type { components } from './types';

export type SyncedEmployee = components['schemas']['SyncedEmployee'];

export interface GetEmployeesParams {
  query?: string;
  department?: string;
  active?: boolean;
}

export async function getEmployees(params?: GetEmployeesParams): Promise<SyncedEmployee[]> {
  const searchParams = new URLSearchParams();
  if (params?.query) searchParams.append('query', params.query);
  if (params?.department) searchParams.append('department', params.department);
  if (params?.active !== undefined) searchParams.append('active', String(params.active));

  const query = searchParams.toString();
  return apiClient<SyncedEmployee[]>(`/employees${query ? `?${query}` : ''}`);
}
