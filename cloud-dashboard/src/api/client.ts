// The cloud API's base URL. In dev, Vite's proxy (vite.config.ts) forwards
// relative paths to the cloud-backend dev server, so this is left empty. In
// a production build, VITE_API_BASE_URL must point at the deployed
// cloud-backend origin — the dashboard and backend are two separately
// deployed services (unlike the local guard PWA, which is served by its own
// backend), so there is no same-origin default to fall back on.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export const getSessionToken = () => sessionStorage.getItem('token');
export const setSessionToken = (token: string) => sessionStorage.setItem('token', token);
export const clearSessionToken = () => sessionStorage.removeItem('token');
export const getSessionUser = () => {
  const user = sessionStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};
export const setSessionUser = (user: any) => sessionStorage.setItem('user', JSON.stringify(user));
export const clearSessionUser = () => sessionStorage.removeItem('user');

/** Shared request path for both JSON and binary (blob) responses: auth
 * header injection, network-failure mapping, and the 401/error-response
 * handling that every endpoint needs, in exactly one place. */
async function fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = getSessionToken();
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(endpoint), { ...options, headers });
  } catch (err: any) {
    throw new ApiError(0, 'network_failure', 'Could not connect to the server. Please check your connection.');
  }

  if (response.status === 401) {
    clearSessionToken();
    clearSessionUser();
    window.dispatchEvent(new Event('auth:unauthorized'));
    const errorData = await response.clone().json().catch(() => ({}));
    throw new ApiError(401, errorData.error || 'unauthorized', errorData.message || 'Unauthorized');
  }

  if (!response.ok) {
    // The real backend always returns a flat { error, message } body (see
    // main.py's exception_handler and every api/*.py router) — never a
    // "detail" key. Reading errorData.error/message directly, not .detail.
    const errorData = await response.clone().json().catch(() => ({}));
    const code = errorData.error || 'unknown_error';
    const message = errorData.message || 'An unknown error occurred';
    throw new ApiError(response.status, code, message);
  }

  return response;
}

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchWithAuth(endpoint, options);
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

/** For endpoints returning a binary body (e.g. the camera-preview JPEG
 * snapshot) rather than JSON. */
export async function apiClientBlob(endpoint: string, options: RequestInit = {}): Promise<Blob> {
  const response = await fetchWithAuth(endpoint, options);
  return response.blob();
}

export interface ErrorDisplay {
  type: 'connection-error' | 'failure' | 'no-face';
  title: string;
  message: string;
}

export function describeError(err: unknown, failureTitle = 'Erreur'): ErrorDisplay {
  if (err instanceof ApiError) {
    if (err.status === 0) {
      return { type: 'connection-error', title: 'Erreur de connexion', message: err.message };
    }
    return { type: 'failure', title: failureTitle, message: err.message };
  }
  return { type: 'failure', title: failureTitle, message: 'Une erreur inattendue est survenue.' };
}
