import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, beforeAll, afterAll, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { EmployeeListPage } from '../../src/pages/EmployeeListPage';
import { server } from '../msw/server';
import React from 'react';

describe('EmployeeListPage Integration', () => {
  afterEach(() => {
    server.resetHandlers();
  });

  const renderApp = () => {
    render(
      <BrowserRouter>
        <EmployeeListPage />
      </BrowserRouter>
    );
  };

  it('renders table and loads data', async () => {
    renderApp();
    
    // Wait for the table to appear and load data
    await waitFor(() => {
      expect(screen.getByText('Alice Dubois')).toBeInTheDocument();
    });
    
    // We mocked Alice and Bob to be active, Charlie to be inactive
    // Default filter is activeOnly=true, so 2 rows should be visible
    expect(screen.getByText('Alice Dubois')).toBeInTheDocument();
    expect(screen.getByText('Bob Martin')).toBeInTheDocument();
    expect(screen.queryByText('Charlie Dupont')).not.toBeInTheDocument();
  });

  it('filters by name', async () => {
    renderApp();
    
    await waitFor(() => {
      expect(screen.getByTestId('employee-table')).toBeInTheDocument();
    });

    const searchInput = screen.getByTestId('search-input');
    fireEvent.change(searchInput, { target: { value: 'alice' } });

    await waitFor(() => {
      expect(screen.getByText('Alice Dubois')).toBeInTheDocument();
      expect(screen.queryByText('Bob Martin')).not.toBeInTheDocument();
    });
  });

  it('filters by department', async () => {
    renderApp();
    
    await waitFor(() => {
      expect(screen.getByTestId('employee-table')).toBeInTheDocument();
    });

    const deptInput = screen.getByTestId('department-input');
    fireEvent.change(deptInput, { target: { value: 'sales' } });

    await waitFor(() => {
      expect(screen.queryByText('Alice Dubois')).not.toBeInTheDocument();
      expect(screen.getByText('Bob Martin')).toBeInTheDocument();
    });
  });

  it('toggles active filter', async () => {
    renderApp();
    
    await waitFor(() => {
      expect(screen.getByTestId('employee-table')).toBeInTheDocument();
    });

    const activeCheckbox = screen.getByTestId('active-checkbox');
    
    // Uncheck active only
    fireEvent.click(activeCheckbox);

    await waitFor(() => {
      // Charlie is inactive, he should now be visible
      expect(screen.getByText('Charlie Dupont')).toBeInTheDocument();
      expect(screen.getByText('Alice Dubois')).toBeInTheDocument();
      expect(screen.getByText('Bob Martin')).toBeInTheDocument();
    });
  });
});
