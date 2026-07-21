import { http, HttpResponse } from 'msw';

export const attendanceHandlers = [
  http.post('/attendance/verify', async ({ request }) => {
    const body = (await request.json()) as any;

    // Simulate different outcomes based on employee_id for testing
    if (body.employee_id === 'emp-success') {
      return HttpResponse.json({
        result: 'success',
        message: 'Attendance recorded',
        verification_attempt: {
          id: 'va-1',
          employee_id: body.employee_id,
          guard_id: 'guard-1',
          type_requested: body.type,
          timestamp: '2026-07-20T22:10:00Z',
          result: 'success',
          similarity_score: 0.95,
          failure_reason: null,
          attendance_event_id: 'ae-1'
        },
        attendance_event: {
          id: 'ae-1',
          employee_id: body.employee_id,
          guard_id: 'guard-1',
          type: body.type,
          timestamp: '2026-07-20T22:10:00Z',
          verification_attempt_id: 'va-1',
          source: 'auto'
        }
      });
    }

    if (body.employee_id === 'emp-failed') {
      return HttpResponse.json({
        result: 'failed',
        message: 'Face verification failed',
        verification_attempt: {
          id: 'va-2',
          employee_id: body.employee_id,
          guard_id: 'guard-1',
          type_requested: body.type,
          timestamp: '2026-07-20T22:15:00Z',
          result: 'failed',
          similarity_score: 0.40,
          failure_reason: 'face_mismatch',
          attendance_event_id: null
        },
        attendance_event: null
      });
    }

    if (body.employee_id === 'emp-duplicate') {
      return HttpResponse.json({
        result: 'duplicate_blocked',
        message: 'Recent attendance was already recorded for this employee',
        verification_attempt: {
          id: 'va-3',
          employee_id: body.employee_id,
          guard_id: 'guard-1',
          type_requested: body.type,
          timestamp: '2026-07-20T22:20:00Z',
          result: 'duplicate_blocked',
          similarity_score: 0.92,
          failure_reason: 'duplicate_recent_attendance',
          attendance_event_id: null
        },
        attendance_event: null
      });
    }

    if (body.employee_id === 'emp-no-face') {
      return HttpResponse.json(
        { detail: { error: 'face_not_detected', message: 'No usable face detected in the capture' } },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      result: 'success',
      message: 'Attendance recorded',
      verification_attempt: {
        id: 'va-default',
        employee_id: body.employee_id,
        guard_id: 'guard-1',
        type_requested: body.type,
        timestamp: '2026-07-20T22:10:00Z',
        result: 'success',
        similarity_score: 0.95,
        failure_reason: null,
        attendance_event_id: 'ae-default'
      },
      attendance_event: {
        id: 'ae-default',
        employee_id: body.employee_id,
        guard_id: 'guard-1',
        type: body.type,
        timestamp: '2026-07-20T22:10:00Z',
        verification_attempt_id: 'va-default',
        source: 'auto'
      }
    });
  }),

  http.get('/attendance/camera-preview', () => {
    return new HttpResponse(new Blob(['fake-jpeg-bytes'], { type: 'image/jpeg' }), {
      headers: { 'Content-Type': 'image/jpeg' }
    });
  }),

  http.get('/attendance/shift-activity', () => {
    return HttpResponse.json([
      {
        kind: 'attendance',
        employee_id: 'emp-1',
        employee_name: 'Ahmed Mohamed',
        type: 'arrival',
        timestamp: '2026-07-20T22:10:00Z',
        guard_username: 'garde1',
        outcome: 'success',
        failure_reason: null,
        attendance_event_id: 'ae-1'
      },
      {
        kind: 'verification',
        employee_id: 'emp-2',
        employee_name: 'Sara Ben Ali',
        type: 'departure',
        timestamp: '2026-07-20T22:15:00Z',
        guard_username: 'garde1',
        outcome: 'failed',
        failure_reason: 'face_mismatch',
        attendance_event_id: null
      },
      {
        kind: 'verification',
        employee_id: 'emp-3',
        employee_name: 'Youssef Kaddour',
        type: 'arrival',
        timestamp: '2026-07-20T22:20:00Z',
        guard_username: 'garde1',
        outcome: 'duplicate_blocked',
        failure_reason: 'duplicate_recent_attendance',
        attendance_event_id: null
      }
    ]);
  })
];
