import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { GoalProgressBar } from '../GoalProgressBar';

describe('GoalProgressBar Component', () => {
  test('renders target and reduction percentages correctly', () => {
    render(<GoalProgressBar reductionPct={10.5} targetPct={15.0} />);

    expect(screen.getByText('Monthly Reduction Goal')).toBeInTheDocument();
    expect(screen.getByText('10.5% reduction achieved')).toBeInTheDocument();
    expect(screen.getByText('Target: 15.0%')).toBeInTheDocument();
    expect(screen.getByText('Keep going!')).toBeInTheDocument();
    expect(screen.queryByText(/Your emissions are currently higher/i)).not.toBeInTheDocument();
  });

  test('renders achieved status when reduction meets or exceeds target', () => {
    render(<GoalProgressBar reductionPct={16.2} targetPct={15.0} />);

    expect(screen.getByText('16.2% reduction achieved')).toBeInTheDocument();
    expect(screen.getByText('Goal Achieved! 🎉')).toBeInTheDocument();
    expect(screen.queryByText('Keep going!')).not.toBeInTheDocument();
  });

  test('renders warning message for negative reduction', () => {
    render(<GoalProgressBar reductionPct={-5.0} targetPct={15.0} />);

    expect(screen.getByText('-5.0% reduction achieved')).toBeInTheDocument();
    expect(screen.getByText('Keep going!')).toBeInTheDocument();
    expect(screen.getByText(/Your emissions are currently higher than your baseline/i)).toBeInTheDocument();
  });

  test('handles zero values and default target fallback', () => {
    render(<GoalProgressBar reductionPct={0} targetPct={0} />);

    expect(screen.getByText('0.0% reduction achieved')).toBeInTheDocument();
    expect(screen.getByText('Target: 15.0%')).toBeInTheDocument(); // fallback to 15.0
  });
});
