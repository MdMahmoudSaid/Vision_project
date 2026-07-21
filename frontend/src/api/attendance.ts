import { apiClient, apiClientBlob } from './client';
import type { components } from './types';

export type AttendanceVerifyRequest = components['schemas']['AttendanceVerifyRequest'];
export type AttendanceVerifyResponse = components['schemas']['AttendanceVerifyResponse'];
export type ShiftActivityItem = components['schemas']['ShiftActivityItem'];

export async function verifyAttendance(payload: AttendanceVerifyRequest): Promise<AttendanceVerifyResponse> {
  return apiClient<AttendanceVerifyResponse>('/attendance/verify', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function getShiftActivity(): Promise<ShiftActivityItem[]> {
  return apiClient<ShiftActivityItem[]>('/attendance/shift-activity', {
    method: 'GET'
  });
}

/** Single-frame JPEG snapshot from the fixed camera, for the guard to confirm
 * framing before verification. Display-only — never used for comparison. */
export async function getCameraPreview(): Promise<Blob> {
  return apiClientBlob('/attendance/camera-preview', { method: 'GET' });
}
