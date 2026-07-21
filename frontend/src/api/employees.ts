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

/** Deletes an employee outright. The backend refuses this (409) if the
 * employee has any attendance/verification history — deactivate them
 * instead in that case (see deactivateEmployee). */
export async function deleteEmployee(employeeId: string): Promise<void> {
  return apiClient<void>(`/employees/${employeeId}`, {
    method: 'DELETE'
  });
}
