import {
  UserCreate,
  UserResponse,
  UserProfile,
  ActivityCreate,
  ActivityResponse,
  NLActivityRequest,
  NLParseResponse,
  CarbonSummary,
  CarbonTrend,
  ProgressReport,
  FootprintSummary,
  AnalysisResult,
  PlanResult,
  Mission
} from '../types/api';

const rawBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const BASE_URL = rawBaseUrl.replace(/\/+$/, '');

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  
  const aiConfigStr = localStorage.getItem('ai_config');
  const aiHeaders: Record<string, string> = {};
  if (aiConfigStr) {
    try {
      const config = JSON.parse(aiConfigStr);
      if (config.provider) aiHeaders['X-AI-Provider'] = config.provider;
      if (config.apiKey) aiHeaders['X-AI-Key'] = config.apiKey;
      if (config.model) aiHeaders['X-AI-Model'] = config.model;
    } catch {}
  }

  const headers = {
    'Content-Type': 'application/json',
    ...aiHeaders,
    ...(options?.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = 'An error occurred';
    try {
      const errData = await response.json();
      detail = errData.detail || detail;
    } catch {
      // Ignore parsing errors
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  users: {
    create: (data: UserCreate) => request<UserResponse>('/api/v1/users', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    get: (userId: string) => request<UserProfile>(`/api/v1/users/${userId}`),
    update: (userId: string, data: UserCreate) => request<UserProfile>(`/api/v1/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    wipeData: (userId: string) => request<{ status: string; message: string }>(`/api/v1/users/${userId}/data`, {
      method: 'DELETE',
    }),
  },
  onboarding: {
    baseline: (data: { user_id: string }) => request<FootprintSummary>('/api/v1/onboarding/baseline', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  },
  activities: {
    log: (data: ActivityCreate) => request<ActivityResponse>('/api/v1/activities', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    parseNL: (data: NLActivityRequest) => request<NLParseResponse>('/api/v1/activities/parse-nl', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    get: (userId: string, page = 1, pageSize = 20, category?: string, date?: string) => {
      let query = `?page=${page}&page_size=${pageSize}`;
      if (category) query += `&category=${category}`;
      if (date) query += `&date=${date}`;
      return request<{ activities: ActivityResponse[]; total: number }>(`/api/v1/activities/${userId}${query}`);
    },
    delete: (activityId: number) => request<{ status: string; message: string }>(`/api/v1/activities/${activityId}`, {
      method: 'DELETE',
    }),
  },
  carbon: {
    summary: (userId: string) => request<CarbonSummary>(`/api/v1/carbon/summary/${userId}`),
    trends: (userId: string, days = 30) => request<CarbonTrend[]>(`/api/v1/carbon/trends/${userId}?days=${days}`),
    progress: (userId: string) => request<ProgressReport>(`/api/v1/carbon/progress/${userId}`),
  },
  agents: {
    insights: (userId: string) => request<{ analyst: AnalysisResult | null; planner: PlanResult | null }>(`/api/v1/agents/insights/${userId}`),
    analyzeUrl: `${BASE_URL}/api/v1/agents/analyze`,
  },
  missions: {
    get: (userId: string) => request<{ pending: Mission[]; active: Mission[]; completed: Mission[] }>(`/api/v1/missions/${userId}`),
    generate: (data: { user_id: string }) => request<Mission[]>('/api/v1/missions/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    accept: (missionId: number) => request<{ status: string; message: string }>(`/api/v1/missions/${missionId}/accept`, {
      method: 'PUT',
    }),
    complete: (missionId: number) => request<{ status: string; message: string }>(`/api/v1/missions/${missionId}/complete`, {
      method: 'POST',
    }),
  },
  chat: {
    streamUrl: `${BASE_URL}/api/v1/chat/stream`,
  }
};
