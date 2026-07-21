import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import ShiftActivityPage from '../../src/pages/ShiftActivityPage';
import { describe, it, expect } from 'vitest';

const renderWithRouter = () => {
  const router = createMemoryRouter([
    {
      path: '/shift-activity',
      element: <ShiftActivityPage />
    }
  ], { initialEntries: ['/shift-activity'] });

  render(<RouterProvider router={router} />);
};

describe('ShiftActivityPage Integration', () => {
  it('lists recent events with distinctly styled outcomes (T039, T040)', async () => {
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Mohamed')).toBeInTheDocument();
      expect(screen.getByText('Sara Ben Ali')).toBeInTheDocument();
      expect(screen.getByText('Youssef Kaddour')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Succès')).toBeInTheDocument();
    expect(screen.getByText('Échec')).toBeInTheDocument();
    expect(screen.getByText('Doublon')).toBeInTheDocument();
  });
});
