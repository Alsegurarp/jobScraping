import type { BotJobsResults, RunRecord, SearchParams } from '@/api/types';

export const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${path}`, options);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new ApiError(payload.detail || `Error HTTP ${response.status}`, response.status);
    }
    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(`No se pudo conectar con ${API_URL}`, 0);
  }
}

function post<T>(path: string, body?: unknown) {
  return request<T>(path, {
    method: 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export const botJobsApi = {
  health: () => request<{ status: string; service: string }>('/health'),
  runs: () => request<RunRecord[]>('/runs?limit=50'),
  run: (runId: string) => request<RunRecord>(`/runs/${runId}`),
  latestResults: () => request<BotJobsResults>('/results/latest'),
  runResults: (runId: string) => request<BotJobsResults>(`/runs/${runId}/results`),
  search: (params: SearchParams) => post<RunRecord>('/runs/search', params),
  extractLinks: (params: { browser: boolean; research: boolean }) =>
    post<RunRecord>('/runs/extract-links', params),
  applyDryRun: () => post<RunRecord>('/runs/apply-approved/dry-run'),
};
