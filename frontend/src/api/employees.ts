import { apiClient } from './client';
import type { components } from './types';

export type EmployeeSummary = components['schemas']['EmployeeSummary'];
export type EmployeeDetail = components['schemas']['EmployeeDetail'];
export type EmployeeCreate = components['schemas']['EmployeeCreate'];
export type FaceEnrollmentRequest = components['schemas']['FaceEnrollmentRequest'];
export type FaceEnrollmentResponse = components['schemas']['FaceEnrollmentResponse'];

export async function searchEmployees(query: string, active: boolean = true): Promise<EmployeeSummary[]> {
  const params = new URLSearchParams({ active: String(active) });
  if (query) {
    params.set('query', query);
  }
  return apiClient<EmployeeSummary[]>(`/employees?${params.toString()}`, {
    method: 'GET'
  });
}

export async function createEmployee(payload: EmployeeCreate): Promise<EmployeeDetail> {
  return apiClient<EmployeeDetail>('/employees', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function enrollFace(
  employeeId: string,
  payload: FaceEnrollmentRequest
): Promise<FaceEnrollmentResponse> {
  return apiClient<FaceEnrollmentResponse>(`/employees/${employeeId}/face`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function deactivateEmployee(employeeId: string): Promise<EmployeeDetail> {
  return apiClient<EmployeeDetail>(`/employees/${employeeId}`, {
    method: 'PATCH',
    body: JSON.stringify({ active: false })
  });
}

/** Deletes an employee outright. Without `force`, the backend refuses this
 * (409) if the employee has any attendance/verification history —
 * deactivate them instead (see deactivateEmployee), or pass `force: true` to
 * delete the employee AND their history permanently (an explicit admin
 * override, not the default). */
export async function deleteEmployee(employeeId: string, force: boolean = false): Promise<void> {
  const params = force ? '?force=true' : '';
  return apiClient<void>(`/employees/${employeeId}${params}`, {
    method: 'DELETE'
  });
}
