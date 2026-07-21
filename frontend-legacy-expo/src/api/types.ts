export type AttendanceType = 'arrival' | 'departure';

export interface Guard {
  id: string;
  username: string;
  fullName: string;
}

export interface Employee {
  id: string;
  employeeNumber: string;
  fullName: string;
  department?: string;
  jobTitle?: string;
  active: boolean;
  faceRegistered: boolean;
}

export interface AttendanceEvent {
  id: string;
  employeeId: string;
  employeeName: string;
  type: AttendanceType;
  timestamp: string;
  guardId: string;
  guardName: string;
}

export interface VerifyFaceResult {
  success: boolean;
  confidence: number;
}
