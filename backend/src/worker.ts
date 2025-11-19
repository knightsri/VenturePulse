import dotenv from 'dotenv';
import { analysisQueue } from './services/queue';
import { ReportGenerator } from './services/reportGenerator';
import { AnalysisJobData } from './types';

// Load environment variables
dotenv.config();

const WORKER_CONCURRENCY = parseInt(process.env.WORKER_CONCURRENCY || '3');

console.log('[Worker] Starting VenturePulse report generation worker');
console.log(`[Worker] Concurrency: ${WORKER_CONCURRENCY}`);
console.log(`[Worker] Environment: ${process.env.NODE_ENV}`);

// Check if analyze-script.sh is available
ReportGenerator.checkScriptAvailability().then((available) => {
  if (!available) {
    console.error('[Worker] Warning: analyze-script.sh not found or not executable');
  } else {
    console.log('[Worker] analyze-script.sh is available');
  }
});

/**
 * Process analysis jobs
 */
analysisQueue.process(WORKER_CONCURRENCY, async (job) => {
  const data: AnalysisJobData = job.data;

  console.log(`[Worker] Processing job ${job.id}`);
  console.log(`[Worker] Project: ${data.projectName}`);
  console.log(`[Worker] Model: ${data.model}`);

  try {
    // Generate report with progress tracking
    const reportPath = await ReportGenerator.generateReport(data, (progress) => {
      // Update job progress
      job.progress(progress);

      console.log(
        `[Worker] Job ${job.id} progress: Section ${progress.currentSection}/${progress.totalSections} - ${progress.sectionName} (${progress.percentage}%)`
      );
    });

    console.log(`[Worker] Job ${job.id} completed successfully`);
    console.log(`[Worker] Report saved to: ${reportPath}`);

    return reportPath;
  } catch (error) {
    console.error(`[Worker] Job ${job.id} failed:`, error);
    throw error;
  }
});

console.log('[Worker] Worker is ready and listening for jobs');

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('[Worker] SIGTERM received, shutting down gracefully');
  await analysisQueue.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('[Worker] SIGINT received, shutting down gracefully');
  await analysisQueue.close();
  process.exit(0);
});

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('[Worker] Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (error) => {
  console.error('[Worker] Unhandled rejection:', error);
  process.exit(1);
});
