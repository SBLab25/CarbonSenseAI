import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import ActivityLogger from '../ActivityLogger';

const logActivityMock = vi.fn();
const parseNLMock = vi.fn();
const deleteActivityMock = vi.fn();

// Mutable state for the mocked user ID
let mockUserId = 'test-user-123';

// Mock the custom hooks
vi.mock('../../hooks/useActivities', () => ({
  useActivities: (userId: string, page: number, pageSize: number) => {
    // If the test triggers history, return some items
    const activities = userId === 'empty-user' ? [] : [
      {
        activity_id: 101,
        user_id: userId,
        category: 'transport',
        type: 'car_petrol',
        amount: 20,
        unit: 'km',
        co2_kg: 4.2,
        source: 'form',
        logged_at: '2026-06-09T20:00:00.000Z'
      }
    ];
    return {
      activities,
      totalCount: activities.length,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
      logActivity: logActivityMock,
      isLogging: false,
      parseNL: parseNLMock,
      isParsing: false,
      deleteActivity: deleteActivityMock,
      isDeleting: false,
    };
  }
}));

// Mock user session
vi.mock('../../lib/user-session', () => ({
  getUserId: () => mockUserId,
}));

describe('ActivityLogger Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUserId = 'test-user-123';
  });

  test('renders tab switcher with Form Input and AI Natural Language tabs', () => {
    render(<ActivityLogger />);
    
    expect(screen.getByText('Form Input')).toBeInTheDocument();
    expect(screen.getByText('AI Natural Language')).toBeInTheDocument();
  });

  test('clicking AI Natural Language tab toggles input components', () => {
    render(<ActivityLogger />);
    
    // Default should show form input fields (e.g. Category select)
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
    expect(screen.queryByLabelText(/Describe your activity/i)).not.toBeInTheDocument();

    // Click NL tab
    fireEvent.click(screen.getByText('AI Natural Language'));
    
    // Now form should be gone and textarea should be present
    expect(screen.queryByLabelText('Category')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Describe your activity/i)).toBeInTheDocument();
  });

  test('renders empty state when no activities are returned', () => {
    mockUserId = 'empty-user';
    
    render(<ActivityLogger />);
    expect(screen.getByText('No activities logged yet.')).toBeInTheDocument();
  });

  test('renders list of recent logged activities', () => {
    mockUserId = 'test-user-123';
    
    render(<ActivityLogger />);
    expect(screen.getAllByText(/car petrol/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/20 km/)).toBeInTheDocument();
    expect(screen.getByText('4.2 kg CO₂')).toBeInTheDocument();
  });
});
