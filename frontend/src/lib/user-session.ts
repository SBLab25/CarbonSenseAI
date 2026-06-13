export const getUserId = (): string | null => {
  return localStorage.getItem('carbonsense_user_id');
};

export const setUserId = (id: string): void => {
  localStorage.setItem('carbonsense_user_id', id);
};

export const clearUserId = (): void => {
  localStorage.removeItem('carbonsense_user_id');
};

export const hasSession = (): boolean => {
  return getUserId() !== null;
};
