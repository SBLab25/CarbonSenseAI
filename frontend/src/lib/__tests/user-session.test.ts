import { describe, test, expect, beforeEach, vi } from 'vitest';
import { getUserId, setUserId, clearUserId, hasSession } from '../user-session';

describe('user-session tests', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  test('hasSession returns false initially when empty', () => {
    expect(hasSession()).toBe(false);
    expect(getUserId()).toBeNull();
  });

  test('setUserId and getUserId performs roundtrip successfully', () => {
    const testId = 'test-session-id-456';
    setUserId(testId);
    
    expect(localStorage.setItem).toHaveBeenCalledWith('carbonsense_user_id', testId);
    expect(getUserId()).toBe(testId);
    expect(localStorage.getItem).toHaveBeenCalledWith('carbonsense_user_id');
  });

  test('hasSession returns true after setUserId has been called', () => {
    setUserId('dummy-id');
    expect(hasSession()).toBe(true);
  });

  test('clearUserId cleans the key from storage', () => {
    setUserId('test-id');
    expect(hasSession()).toBe(true);
    
    clearUserId();
    expect(localStorage.removeItem).toHaveBeenCalledWith('carbonsense_user_id');
    expect(hasSession()).toBe(false);
    expect(getUserId()).toBeNull();
  });
});
