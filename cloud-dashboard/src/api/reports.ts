import { apiClient, apiClientBlob } from './client';
import type { components } from './types';

export type Report = components['schemas']['Report'];

export interface ReportParams {
  type: 'daily' | 'weekly' | 'monthly' | 'custom';
  date?: string;
  week_start?: string;
  month?: string;
  date_from?: string;
  date_to?: string;
  employee_id?: string;
}

function buildReportSearchParams(params: ReportParams): URLSearchParams {
  const searchParams = new URLSearchParams();
  if (params.date) searchParams.append('date', params.date);
  if (params.week_start) searchParams.append('week_start', params.week_start);
  if (params.month) searchParams.append('month', params.month);
  if (params.date_from) searchParams.append('date_from', params.date_from);
  if (params.date_to) searchParams.append('date_to', params.date_to);
  if (params.employee_id) searchParams.append('employee_id', params.employee_id);
  return searchParams;
}

export async function fetchReport(params: ReportParams): Promise<Report> {
  const searchParams = buildReportSearchParams(params);
  return apiClient<Report>(`/reports/${params.type}?${searchParams.toString()}`);
}

export async function downloadReport(params: ReportParams & { format: 'pdf' | 'xlsx' }): Promise<Blob> {
  const searchParams = buildReportSearchParams(params);
  searchParams.append('type', params.type);
  searchParams.append('format', params.format);

  return apiClientBlob(`/reports/export?${searchParams.toString()}`);
}
