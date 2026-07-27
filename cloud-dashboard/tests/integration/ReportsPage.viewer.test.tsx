import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { SessionProvider } from '../../src/auth/SessionContext';
import { ReportsPage } from '../../src/pages/ReportsPage';
import { server } from '../msw/server';
import React from 'react';

// Mock getSessionUser and getSessionToken to control the session role
import * as clientModule from '../../src/api/client';
import { vi } from 'vitest';

describe('ReportsPage Integration', () => {
  afterEach(() => {
    server.resetHandlers();
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  const renderApp = () => {
    render(
      <SessionProvider>
        <BrowserRouter>
          <ReportsPage />
        </BrowserRouter>
      </SessionProvider>
    );
  };

  it('allows Viewer to select parameters, generate, export, and print reports but hides data-modifying controls', async () => {
    // Mock user session as Viewer
    vi.spyOn(clientModule, 'getSessionUser').mockReturnValue({
      id: 'viewer-1',
      email: 'viewer@example.com',
      role: 'viewer',
      active: true
    });
    vi.spyOn(clientModule, 'getSessionToken').mockReturnValue('fake-token');

    renderApp();

    // Verify selectors exist
    expect(screen.getByTestId('report-type-select')).toBeInTheDocument();
    
    // Choose Daily, fill date, click generate
    const dateInput = screen.getByTestId('date-input');
    fireEvent.change(dateInput, { target: { value: '2026-07-27' } });

    const generateBtn = screen.getByTestId('generate-btn');
    fireEvent.click(generateBtn);

    // Wait for report table to render
    await waitFor(() => {
      expect(screen.getByTestId('report-table')).toBeInTheDocument();
    });

    // Check data row renders
    expect(screen.getByText('Alice Dubois')).toBeInTheDocument();

    // Check export and print buttons exist
    expect(screen.getByTestId('export-pdf-btn')).toBeInTheDocument();
    expect(screen.getByTestId('export-excel-btn')).toBeInTheDocument();
    expect(screen.getByTestId('print-btn')).toBeInTheDocument();

    // Viewer should NOT see any "Corriger" button or other modifying controls
    expect(screen.queryByText('Corriger')).not.toBeInTheDocument();
  });

  it('shows Corriger button for Admin / Owner', async () => {
    // Mock user session as Admin
    vi.spyOn(clientModule, 'getSessionUser').mockReturnValue({
      id: 'admin-1',
      email: 'admin@example.com',
      role: 'admin',
      active: true
    });
    vi.spyOn(clientModule, 'getSessionToken').mockReturnValue('fake-token');

    renderApp();

    const dateInput = screen.getByTestId('date-input');
    fireEvent.change(dateInput, { target: { value: '2026-07-27' } });

    const generateBtn = screen.getByTestId('generate-btn');
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(screen.getByTestId('report-table')).toBeInTheDocument();
    });

    // Admin should see the "Corriger" button
    expect(screen.getByText('Corriger')).toBeInTheDocument();
  });
});
