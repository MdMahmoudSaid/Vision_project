import { apiClient } from './client';
import type { components } from './types';

export type CloudUser = components['schemas']['CloudUser'];
export type CloudUserInvite = components['schemas']['CloudUserInvite'];
export type CloudUserUpdate = components['schemas']['CloudUserUpdate'];

export async function getUsers(): Promise<CloudUser[]> {
  return apiClient<CloudUser[]>('/users');
}

export async function inviteUser(payload: CloudUserInvite): Promise<CloudUser> {
  return apiClient<CloudUser>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateUser(userId: string, payload: CloudUserUpdate): Promise<CloudUser> {
  return apiClient<CloudUser>(`/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteUser(userId: string): Promise<void> {
  await apiClient<void>(`/users/${userId}`, { method: 'DELETE' });
}
