// Job types for Bull queue
export interface AnalysisJobData {
  jobId: string;
  projectName: string;
  projectContent: string;
  model: string;
  userId?: string;
  ideaId?: string;
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
  startedAt?: Date;
  completedAt?: Date;
  estimatedCompletion?: Date;
  error?: string;
  reportPath?: string;
}

// OpenRouter model types
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

// Report types
export interface ReportMetadata {
  id: string;
  projectName: string;
  model: string;
  createdAt: Date;
  status: 'generating' | 'completed' | 'failed';
  path: string;
  ideaId?: string;
  userId?: string;
}

// Analysis request
export interface AnalysisRequest {
  projectName: string;
  projectContent?: string;
  file?: Express.Multer.File;
  models: string[];
  ideaId?: string;
  userId?: string;
}

// Analysis response
export interface AnalysisResponse {
  jobIds: string[];
  message: string;
}
