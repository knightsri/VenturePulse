import Queue from 'bull';
import { AnalysisJobData } from '../types';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

// Create analysis queue
export const analysisQueue = new Queue<AnalysisJobData>('analysis', REDIS_URL, {
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
    removeOnComplete: false,
    removeOnFail: false,
  },
});

// Queue event listeners
analysisQueue.on('completed', (job) => {
  console.log(`[Queue] Job ${job.id} completed successfully`);
});

analysisQueue.on('failed', (job, err) => {
  console.error(`[Queue] Job ${job?.id} failed:`, err.message);
});

analysisQueue.on('error', (error) => {
  console.error('[Queue] Error:', error);
});

analysisQueue.on('waiting', (jobId) => {
  console.log(`[Queue] Job ${jobId} is waiting`);
});

analysisQueue.on('active', (job) => {
  console.log(`[Queue] Job ${job.id} is now active`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('[Queue] Closing queue...');
  await analysisQueue.close();
  process.exit(0);
});

export default analysisQueue;
