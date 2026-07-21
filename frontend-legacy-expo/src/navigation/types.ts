import { AttendanceType } from '../api/types';

export type RootStackParamList = {
  Login: undefined;
  EmployeeSearch: undefined;
  EmployeeDetail: { employeeId: string };
  VerifyFace: { employeeId: string; type: AttendanceType };
  Confirmation: { employeeName: string; type: AttendanceType; timestamp: string };
  ShiftActivity: undefined;
};
