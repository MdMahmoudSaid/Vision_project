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
    response = await fetch(endpoint, { ...options, headers });
  } catch (err: any) {
    throw new ApiError(0, 'network_failure', 'Could not connect to the local server. Please check your connection.');
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
  type: 'connection-error' | 'failure' | 'no-face' | 'spoof';
  title: string;
  message: string;
}

// Backend error codes meaning "we got frames from the camera, but never a
// clear enough face" (enrollment: no_face_detected; verification:
// face_not_detected). These get a distinct, actionable message rather than
// the generic failure banner, since the fix is simply repositioning.
const NO_FACE_ERROR_CODES = new Set(['no_face_detected', 'face_not_detected']);

/** Shared mapping from a caught error to a display state, used by every page
 * that shows a result banner, so the connection-error/failure distinction
 * (status 0 vs any other ApiError) is made in exactly one place. */
export function describeError(err: unknown, failureTitle = 'Erreur'): ErrorDisplay {
  if (err instanceof ApiError) {
    if (err.status === 0) {
      return { type: 'connection-error', title: 'Erreur de connexion', message: err.message };
    }
    if (err.code === 'spoof_detected') {
      return {
        type: 'spoof',
        title: 'Visage non authentifié',
        message: "La caméra a détecté une photo ou un écran plutôt qu'un visage réel. Présentez-vous directement devant la caméra et réessayez."
      };
    }
    if (NO_FACE_ERROR_CODES.has(err.code)) {
      return {
        type: 'no-face',
        title: 'Aucun visage détecté',
        message: "Assurez-vous que le visage est bien visible, centré et bien éclairé face à la caméra, puis réessayez."
      };
    }
    return { type: 'failure', title: failureTitle, message: err.message };
  }
  return { type: 'failure', title: failureTitle, message: 'Une erreur inattendue est survenue.' };
}
