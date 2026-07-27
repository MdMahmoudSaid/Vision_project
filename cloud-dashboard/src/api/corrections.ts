import { apiClient } from './client';
import type { components } from './types';

export type Correction = components['schemas']['Correction'];
export type CorrectionCreate = components['schemas']['CorrectionCreate'];
export type EmployeeAttendanceHistory = components['schemas']['EmployeeAttendanceHistory'];

export async function createCorrection(payload: CorrectionCreate): Promise<Correction> {
  return apiClient<Correction>('/attendance/corrections', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getCorrectionsForEmployee(employeeId: string): Promise<Correction[]> {
  return apiClient<Correction[]>(`/attendance/corrections/${employeeId}`);
}

export async function getEmployeeAttendanceHistory(
  employeeId: string,
  dateFrom?: string,
  dateTo?: string
): Promise<EmployeeAttendanceHistory> {
  const searchParams = new URLSearchParams();
  if (dateFrom) searchParams.append('date_from', dateFrom);
  if (dateTo) searchParams.append('date_to', dateTo);
  const query = searchParams.toString();
  return apiClient<EmployeeAttendanceHistory>(`/employees/${employeeId}/attendance${query ? `?${query}` : ''}`);
}
