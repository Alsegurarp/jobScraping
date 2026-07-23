import { fetch as expoFetch } from 'expo/fetch';
import { File as ExpoFile } from 'expo-file-system';

import type { BotJobsResults, CvDocument, RunRecord, SearchParams } from '@/api/types';

export const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const response = await expoFetch(`${API_URL}${path}`, options);
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

type CvUpload = { uri: string; name: string; mimeType?: string | null; file?: Blob };

function uploadCv(file: CvUpload) {
  const body = file.file || new ExpoFile(file.uri);
  return request<CvDocument>(`/documents/cv?filename=${encodeURIComponent(file.name)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/pdf' },
    body: body as unknown as BodyInit,
  });
}

export const botJobsApi = {
  health: () => request<{ status: string; service: string }>('/health'),
  runs: () => request<RunRecord[]>('/runs?limit=50'),
  run: (runId: string) => request<RunRecord>(`/runs/${runId}`),
  latestResults: () => request<BotJobsResults>('/results/latest'),
  runResults: (runId: string) => request<BotJobsResults>(`/runs/${runId}/results`),
  letter: (letterId: string) => request<{ letter_id: string; content: string }>(`/letters/${encodeURIComponent(letterId)}`),
  cvs: () => request<CvDocument[]>('/documents/cv'),
  uploadCv,
  activateCv: (cvId: string) => post<CvDocument>(`/documents/cv/${encodeURIComponent(cvId)}/active`),
  cvUrl: (cvId: string) => `${API_URL}/documents/cv/${encodeURIComponent(cvId)}`,
  decideJob: (body: { url: string; decision: 'aprobada' | 'descartada' | 'revision'; note?: string; cv_id?: string }) => post('/jobs/decision', body),
  search: (params: SearchParams) => post<RunRecord>('/runs/search', params),
  extractLinks: (params: { browser: boolean; research: boolean }) =>
    post<RunRecord>('/runs/extract-links', params),
  applyDryRun: () => post<RunRecord>('/runs/apply-approved/dry-run'),
  prepareApplications: () => post<RunRecord>('/runs/apply-approved/prepare'),
  retryApplications: () => post<RunRecord>('/runs/apply-approved/retry'),
  submitApplications: () => post<RunRecord>('/runs/apply-approved/submit', { confirmation: 'ENVIAR' }),
  evidenceUrl: (evidenceId: string) => `${API_URL}/evidence/${encodeURIComponent(evidenceId)}`,
};
