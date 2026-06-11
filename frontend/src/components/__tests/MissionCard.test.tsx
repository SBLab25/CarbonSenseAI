import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { MissionCard } from '../MissionCard';
import { Mission } from '../../types/api';

describe('MissionCard Component', () => {
  const baseMission: Mission = {
    id: 1,
    user_id: 'user-123',
    title: 'Eat Plant-Based',
    description: 'Replace meat with plant-based alternatives for one day.',
    category: 'food',
    target_reduction_kg: 2.5,
    eco_points_reward: 150,
    status: 'pending',
    created_at: '2026-06-09T12:00:00.000Z',
  };

  test('renders pending mission with Accept button', () => {
    const onAcceptMock = vi.fn();
    render(
      <MissionCard
        mission={baseMission}
        onAccept={onAcceptMock}
      />
    );

    expect(screen.getByText('Eat Plant-Based')).toBeInTheDocument();
    expect(screen.getByText('Replace meat with plant-based alternatives for one day.')).toBeInTheDocument();
    expect(screen.getByText('+150 pts')).toBeInTheDocument();
    expect(screen.getByText(/2.5 kg/i)).toBeInTheDocument();

    const acceptBtn = screen.getByRole('button', { name: /Accept Challenge/i });
    expect(acceptBtn).toBeInTheDocument();
    fireEvent.click(acceptBtn);
    expect(onAcceptMock).toHaveBeenCalledWith(baseMission.id);
  });

  test('renders active mission with Complete button and countdown', () => {
    const onCompleteMock = vi.fn();
    // Set deadline to 3 days from now
    const threeDaysFromNow = new Date();
    threeDaysFromNow.setDate(threeDaysFromNow.getDate() + 3);

    const activeMission: Mission = {
      ...baseMission,
      status: 'active',
      deadline: threeDaysFromNow.toISOString(),
    };

    render(
      <MissionCard
        mission={activeMission}
        onComplete={onCompleteMock}
      />
    );

    const completeBtn = screen.getByRole('button', { name: /Complete Challenge/i });
    expect(completeBtn).toBeInTheDocument();
    expect(screen.getByText(/3 days left/i)).toBeInTheDocument();

    fireEvent.click(completeBtn);
    expect(onCompleteMock).toHaveBeenCalledWith(activeMission.id);
  });

  test('renders expired mission state', () => {
    const expiredDate = new Date();
    expiredDate.setDate(expiredDate.getDate() - 1);

    const expiredMission: Mission = {
      ...baseMission,
      status: 'active',
      deadline: expiredDate.toISOString(),
    };

    render(<MissionCard mission={expiredMission} />);

    expect(screen.getByText('Challenge Expired')).toBeInTheDocument();
    expect(screen.getByText('Expired')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  test('renders completed mission state', () => {
    const completedMission: Mission = {
      ...baseMission,
      status: 'completed',
      completed_at: '2026-06-09T18:00:00.000Z',
    };

    render(<MissionCard mission={completedMission} />);

    expect(screen.getByText('Challenge Achieved')).toBeInTheDocument();
    expect(screen.getByText(/Completed on/i)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  test('disables action button when isActionLoading is true', () => {
    render(
      <MissionCard
        mission={baseMission}
        onAccept={vi.fn()}
        isActionLoading={true}
      />
    );

    const acceptBtn = screen.getByRole('button', { name: /Accept Challenge/i });
    expect(acceptBtn).toBeDisabled();
  });
});
