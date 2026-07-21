import { AttendanceEvent, AttendanceType, Employee, Guard, VerifyFaceResult } from './types';

/**
 * Stand-in for the real backend. Every function has the same shape a real
 * fetch() call would have (async, throws on failure) so swapping in the
 * actual API later only means changing this file's implementation.
 */

const DELAY_MS = 500;

function delay<T>(value: T, ms = DELAY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

const guards: Array<Guard & { password: string }> = [
  { id: 'g1', username: 'guard1', password: 'password', fullName: 'Yacoub Sidi' },
  { id: 'g2', username: 'guard2', password: 'password', fullName: 'Mariem Salem' },
];

let employees: Employee[] = [
  { id: 'e1', employeeNumber: '1001', fullName: 'Ahmed Mohamed', department: 'Warehouse', jobTitle: 'Operator', active: true, faceRegistered: true },
  { id: 'e2', employeeNumber: '1002', fullName: 'Fatima Zahra', department: 'Reception', jobTitle: 'Receptionist', active: true, faceRegistered: true },
  { id: 'e3', employeeNumber: '1003', fullName: 'Omar El Idrissi', department: 'Maintenance', jobTitle: 'Technician', active: true, faceRegistered: true },
  { id: 'e4', employeeNumber: '1004', fullName: 'Khadija Bint Salem', department: 'Warehouse', jobTitle: 'Supervisor', active: true, faceRegistered: false },
  { id: 'e5', employeeNumber: '1005', fullName: 'Youssef Hadrami', department: 'Security', jobTitle: 'Guard', active: true, faceRegistered: true },
];

const attendanceEvents: AttendanceEvent[] = [];
const recentSubmissions = new Map<string, number>();
const DUPLICATE_WINDOW_MS = 10_000;

let currentToken: string | null = null;
let currentGuard: Guard | null = null;

export async function login(username: string, password: string): Promise<{ token: string; guard: Guard }> {
  const match = guards.find((g) => g.username === username && g.password === password);
  if (!match) {
    return delay(null).then(() => {
      throw new Error('Invalid username or password');
    });
  }
  const { password: _pw, ...guard } = match;
  currentToken = `mock-token-${guard.id}`;
  currentGuard = guard;
  return delay({ token: currentToken, guard });
}

export async function logout(): Promise<void> {
  currentToken = null;
  currentGuard = null;
  return delay(undefined, 100);
}

export function getSession(): { token: string; guard: Guard } | null {
  if (!currentToken || !currentGuard) return null;
  return { token: currentToken, guard: currentGuard };
}

export async function searchEmployees(query: string): Promise<Employee[]> {
  const q = query.trim().toLowerCase();
  const results = !q
    ? employees.filter((e) => e.active)
    : employees.filter(
        (e) => e.active && (e.fullName.toLowerCase().includes(q) || e.employeeNumber.includes(q))
      );
  return delay(results, 300);
}

export async function getEmployee(id: string): Promise<Employee> {
  const employee = employees.find((e) => e.id === id);
  if (!employee) {
    return delay(null).then(() => {
      throw new Error('Employee not found');
    });
  }
  return delay(employee, 150);
}

/**
 * Simulates on-device face matching. Always "succeeds" for the mock so the
 * happy path is easy to demo; occasionally fails so the retry flow is
 * exercised too.
 */
export async function verifyFace(employeeId: string, _photoUri: string): Promise<VerifyFaceResult> {
  const employee = employees.find((e) => e.id === employeeId);
  if (!employee?.faceRegistered) {
    return delay({ success: false, confidence: 0 }, 800);
  }
  const success = Math.random() > 0.15;
  const confidence = success ? 0.85 + Math.random() * 0.15 : Math.random() * 0.5;
  return delay({ success, confidence }, 900);
}

export async function recordAttendance(
  employeeId: string,
  type: AttendanceType,
  guard: Guard
): Promise<AttendanceEvent> {
  const employee = employees.find((e) => e.id === employeeId);
  if (!employee) throw new Error('Employee not found');

  const dedupeKey = `${employeeId}:${type}`;
  const lastSubmission = recentSubmissions.get(dedupeKey);
  const now = Date.now();
  if (lastSubmission && now - lastSubmission < DUPLICATE_WINDOW_MS) {
    throw new Error('This attendance event was just recorded. Please wait before trying again.');
  }
  recentSubmissions.set(dedupeKey, now);

  const event: AttendanceEvent = {
    id: `att-${now}-${Math.round(Math.random() * 1000)}`,
    employeeId,
    employeeName: employee.fullName,
    type,
    timestamp: new Date().toISOString(),
    guardId: guard.id,
    guardName: guard.fullName,
  };
  attendanceEvents.unshift(event);
  return delay(event, 200);
}

export async function getShiftActivity(guardId: string): Promise<AttendanceEvent[]> {
  return delay(
    attendanceEvents.filter((e) => e.guardId === guardId),
    200
  );
}
