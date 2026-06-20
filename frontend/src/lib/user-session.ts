/**
 * User session management — stores and retrieves the session UUID from
 * localStorage. No authentication is used; the UUID is the sole identifier
 * for the current user's data in the backend.
 */

/** @returns The current session user UUID, or null if not set. */
export const getUserId = (): string | null => {
  return localStorage.getItem('carbonsense_user_id');
};

/** Sets the session user UUID in localStorage. */
export const setUserId = (id: string): void => {
  localStorage.setItem('carbonsense_user_id', id);
};

/** Removes the session user UUID (effectively logs out). */
export const clearUserId = (): void => {
  localStorage.removeItem('carbonsense_user_id');
};

/** @returns True if a session UUID is present in localStorage. */
export const hasSession = (): boolean => {
  return getUserId() !== null;
};
