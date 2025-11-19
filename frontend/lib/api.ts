import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = error.response?.data
      ? (error.response.data as any).error?.message || 'An error occurred'
      : error.message;

    console.error('[API Error]', message);
    return Promise.reject(new Error(message));
  }
);

// Types
export interface OpenRouterModel {
  id: string;
  name: string;
  provider: string;
  pricing: {
    prompt: number;
    completion: number;
  };
  contextLength: number;
  estimatedCost?: number;
  speed?: 'slow' | 'medium' | 'fast';
  recommended?: boolean;
}

export interface JobProgress {
  currentSection: number;
  totalSections: number;
  sectionName: string;
  percentage: number;
}

export interface JobStatus {
  jobId: string;
  status: 'waiting' | 'active' | 'completed' | 'failed';
  progress?: JobProgress;
  startedAt?: string;
  completedAt?: string;
  estimatedCompletion?: string;
  error?: string;
  reportPath?: string;
}

export interface ReportMetadata {
  id: string;
  projectName: string;
  model: string;
  createdAt: string;
  status: 'generating' | 'completed' | 'failed';
  path: string;
}

export interface Idea {
  id: string;
  name: string;
  description: string;
  industry?: string;
  targetMarket?: string;
  estimatedBudget?: number;
  tags: string[];
  notes?: string;
  status: 'DRAFT' | 'ANALYZING' | 'ANALYZED' | 'ARCHIVED';
  createdAt: string;
  updatedAt: string;
  versions?: IdeaVersion[];
  reports?: ReportMetadata[];
}

export interface IdeaVersion {
  id: string;
  ideaId: string;
  version: number;
  description: string;
  changes: string;
  createdAt: string;
}

export interface CreateIdeaRequest {
  name: string;
  description: string;
  industry?: string;
  targetMarket?: string;
  estimatedBudget?: number;
  tags?: string[];
  notes?: string;
}

export interface UpdateIdeaRequest extends CreateIdeaRequest {
  changes: string;
}

export interface ScoreData {
  market: number;
  technical: number;
  competitive: number;
  business: number;
  execution: number;
  overall: number;
}

export interface ModelComparison {
  model: string;
  reportId: string;
  scores: ScoreData;
  verdict: string;
  cost: number;
  createdAt: string;
}

export interface ComparisonResult {
  ideaName: string;
  models: ModelComparison[];
  averageScores: ScoreData;
  scoreSpread: ScoreData;
  consensus: string[];
  disagreements: string[];
  recommendation: string;
  costVsQuality: {
    bestValue: string;
    highestQuality: string;
    lowestCost: string;
  };
}

export interface AnalysisRequest {
  projectName: string;
  projectContent?: string;
  file?: File;
  models: string[];
}

export interface AnalysisResponse {
  jobIds: string[];
  message: string;
}

// API Functions

/**
 * Fetch available models from OpenRouter
 */
export async function fetchModels(): Promise<OpenRouterModel[]> {
  const response = await apiClient.get('/api/models');
  return response.data.models;
}

/**
 * Submit a project for analysis
 */
export async function submitAnalysis(data: AnalysisRequest): Promise<AnalysisResponse> {
  const formData = new FormData();

  formData.append('projectName', data.projectName);
  formData.append('models', JSON.stringify(data.models));

  if (data.file) {
    formData.append('file', data.file);
  } else if (data.projectContent) {
    formData.append('projectContent', data.projectContent);
  }

  const response = await apiClient.post('/api/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Get job status
 */
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await apiClient.get(`/api/jobs/${jobId}`);
  return response.data;
}

/**
 * Cancel a job
 */
export async function cancelJob(jobId: string): Promise<void> {
  await apiClient.delete(`/api/jobs/${jobId}`);
}

/**
 * Fetch all reports
 */
export async function fetchReports(): Promise<ReportMetadata[]> {
  const response = await apiClient.get('/api/reports');
  return response.data.reports;
}

/**
 * Delete a report
 */
export async function deleteReport(reportId: string): Promise<void> {
  await apiClient.delete(`/api/reports/${reportId}`);
}

/**
 * Get report URL
 */
export function getReportUrl(reportId: string, format: 'html' | 'zip' = 'html'): string {
  return `${API_BASE_URL}/api/reports/${reportId}?format=${format}`;
}

/**
 * Stream job progress via Server-Sent Events
 */
export function streamJobProgress(
  jobId: string,
  onProgress: (progress: JobProgress) => void,
  onComplete: (reportPath: string) => void,
  onError: (error: string) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE_URL}/api/jobs/${jobId}/stream`);

  eventSource.addEventListener('progress', (event) => {
    const data = JSON.parse(event.data);
    onProgress(data);
  });

  eventSource.addEventListener('complete', (event) => {
    const data = JSON.parse(event.data);
    onComplete(data.reportPath);
    eventSource.close();
  });

  eventSource.addEventListener('error', (event) => {
    const data = JSON.parse(event.data);
    onError(data.message);
    eventSource.close();
  });

  eventSource.onerror = () => {
    onError('Connection lost');
    eventSource.close();
  };

  // Return cleanup function
  return () => {
    eventSource.close();
  };
}

/**
 * Ideas API Functions
 */

/**
 * Fetch all ideas
 */
export async function fetchIdeas(params?: {
  search?: string;
  status?: string;
  industry?: string;
  limit?: number;
  offset?: number;
}): Promise<Idea[]> {
  const response = await apiClient.get('/api/ideas', { params });
  return response.data.ideas;
}

/**
 * Fetch a single idea by ID
 */
export async function fetchIdea(ideaId: string): Promise<Idea> {
  const response = await apiClient.get(`/api/ideas/${ideaId}`);
  return response.data.idea;
}

/**
 * Create a new idea
 */
export async function createIdea(data: CreateIdeaRequest): Promise<Idea> {
  const response = await apiClient.post('/api/ideas', data);
  return response.data.idea;
}

/**
 * Update an existing idea
 */
export async function updateIdea(ideaId: string, data: UpdateIdeaRequest): Promise<Idea> {
  const response = await apiClient.put(`/api/ideas/${ideaId}`, data);
  return response.data.idea;
}

/**
 * Delete an idea
 */
export async function deleteIdea(ideaId: string): Promise<void> {
  await apiClient.delete(`/api/ideas/${ideaId}`);
}

/**
 * Analyze an idea
 */
export async function analyzeIdea(ideaId: string, models: string[]): Promise<AnalysisResponse> {
  const response = await apiClient.post(`/api/ideas/${ideaId}/analyze`, { models });
  return response.data;
}

/**
 * Fetch reports for an idea
 */
export async function fetchIdeaReports(ideaId: string): Promise<ReportMetadata[]> {
  const response = await apiClient.get(`/api/ideas/${ideaId}/reports`);
  return response.data.reports;
}

/**
 * Comparison API Functions
 */

/**
 * Compare specific reports
 */
export async function compareReports(reportIds: string[]): Promise<ComparisonResult> {
  const response = await apiClient.get('/api/compare', {
    params: { reports: reportIds.join(',') },
  });
  return response.data.comparison;
}

/**
 * Compare all reports for an idea
 */
export async function compareIdeaReports(ideaId: string): Promise<ComparisonResult> {
  const response = await apiClient.get(`/api/compare/idea/${ideaId}`);
  return response.data.comparison;
}

/**
 * Compare latest reports for a project
 */
export async function compareLatestReports(projectName: string): Promise<ComparisonResult> {
  const response = await apiClient.get('/api/compare/latest', {
    params: { projectName },
  });
  return response.data.comparison;
}

export default apiClient;
