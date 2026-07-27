import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, afterEach, vi } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { SessionProvider } from '../../src/auth/SessionContext';
import { EmployeeHistoryPage } from '../../src/pages/EmployeeHistoryPage';
import * as clientModule from '../../src/api/client';
import React from 'react';

describe('EmployeeHistoryPage correction flow', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  const renderApp = () => {
    render(
      <SessionProvider>
        <MemoryRouter initialEntries={['/employees/emp-1/history']}>
          <Routes>
            <Route path="/employees/:id/history" element={<EmployeeHistoryPage />} />
          </Routes>
        </MemoryRouter>
      </SessionProvider>
    );
  };

  it('lets an Admin add a missing-departure correction and see it reflected in the audit trail', async () => {
    vi.spyOn(clientModule, 'getSessionUser').mockReturnValue({
      id: 'admin-1',
      email: 'admin@example.com',
      role: 'admin',
      active: true,
    });
    vi.spyOn(clientModule, 'getSessionToken').mockReturnValue('fake-token');

    renderApp();

    await waitFor(() => {
      expect(screen.getByTestId('history-table')).toBeInTheDocument();
    });

    // Missing-departure day is visible from the history fixture.
    expect(screen.getByText('missing_departure')).toBeInTheDocument();

    fireEvent.change(screen.getByTestId('correction-action-select'), { target: { value: 'add_departure' } });
    fireEvent.change(screen.getByTestId('correction-timestamp-input'), { target: { value: '2026-07-27T17:00' } });
    fireEvent.change(screen.getByTestId('correction-reason-input'), {
      target: { value: 'Guard forgot to trigger departure verification' },
    });
    fireEvent.click(screen.getByTestId('correction-submit-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('audit-trail-table')).toBeInTheDocument();
    });
    expect(screen.getByText(/Guard forgot to trigger departure verification/i)).toBeInTheDocument();
  });

  it('lets an Admin correct a timestamp on an existing event', async () => {
    vi.spyOn(clientModule, 'getSessionUser').mockReturnValue({
      id: 'admin-1',
      email: 'admin@example.com',
      role: 'admin',
      active: true,
    });
    vi.spyOn(clientModule, 'getSessionToken').mockReturnValue('fake-token');

    renderApp();

    await waitFor(() => {
      expect(screen.getByTestId('history-table')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('correction-action-select'), { target: { value: 'correct_time' } });
    fireEvent.change(screen.getByTestId('correction-event-id-input'), { target: { value: 'evt-1' } });
    fireEvent.change(screen.getByTestId('correction-timestamp-input'), { target: { value: '2026-07-27T08:30' } });
    fireEvent.change(screen.getByTestId('correction-reason-input'), {
      target: { value: 'NVR shows a different arrival time' },
    });
    fireEvent.click(screen.getByTestId('correction-submit-btn'));

    await waitFor(() => {
      expect(screen.getByText(/NVR shows a different arrival time/i)).toBeInTheDocument();
    });
  });

  it('does not show the correction form to a Viewer', async () => {
    vi.spyOn(clientModule, 'getSessionUser').mockReturnValue({
      id: 'viewer-1',
      email: 'viewer@example.com',
      role: 'viewer',
      active: true,
    });
    vi.spyOn(clientModule, 'getSessionToken').mockReturnValue('fake-token');

    renderApp();

    await waitFor(() => {
      expect(screen.getByTestId('history-table')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('correction-submit-btn')).not.toBeInTheDocument();
  });
});
