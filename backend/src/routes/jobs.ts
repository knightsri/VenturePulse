import express from 'express';
import { analysisQueue } from '../services/queue';
import { JobStatus } from '../types';

const router = express.Router();

/**
 * GET /api/jobs/:jobId
 * Get job status
 */
router.get('/:jobId', async (req, res, next) => {
  try {
    const { jobId } = req.params;

    const job = await analysisQueue.getJob(jobId);

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    const state = await job.getState();
    const progress = job.progress();

    const status: JobStatus = {
      jobId: job.id as string,
      status: state as any,
      progress: typeof progress === 'object' ? progress : undefined,
      startedAt: job.processedOn ? new Date(job.processedOn) : undefined,
      completedAt: job.finishedOn ? new Date(job.finishedOn) : undefined,
      error: job.failedReason,
      reportPath: job.returnvalue,
    };

    // Estimate completion time if job is active
    if (state === 'active' && typeof progress === 'object' && progress.percentage) {
      const elapsed = Date.now() - (job.processedOn || Date.now());
      const estimatedTotal = (elapsed / progress.percentage) * 100;
      const remaining = estimatedTotal - elapsed;
      status.estimatedCompletion = new Date(Date.now() + remaining);
    }

    res.json(status);
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/jobs/:jobId/stream
 * Server-Sent Events endpoint for real-time progress updates
 */
router.get('/:jobId/stream', async (req, res, next) => {
  const { jobId } = req.params;

  // Set headers for SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  // Send initial connection message
  res.write(`data: ${JSON.stringify({ type: 'connected', jobId })}\n\n`);

  let checkInterval: NodeJS.Timeout;

  try {
    // Check job status periodically
    checkInterval = setInterval(async () => {
      try {
        const job = await analysisQueue.getJob(jobId);

        if (!job) {
          res.write(`event: error\ndata: ${JSON.stringify({ message: 'Job not found' })}\n\n`);
          res.end();
          clearInterval(checkInterval);
          return;
        }

        const state = await job.getState();
        const progress = job.progress();

        // Send progress update
        if (state === 'active' && typeof progress === 'object') {
          res.write(`event: progress\ndata: ${JSON.stringify(progress)}\n\n`);
        }

        // Send completion event
        if (state === 'completed') {
          res.write(`event: complete\ndata: ${JSON.stringify({
            reportPath: job.returnvalue,
            jobId,
          })}\n\n`);
          res.end();
          clearInterval(checkInterval);
        }

        // Send error event
        if (state === 'failed') {
          res.write(`event: error\ndata: ${JSON.stringify({
            message: job.failedReason || 'Job failed',
            jobId,
          })}\n\n`);
          res.end();
          clearInterval(checkInterval);
        }
      } catch (error) {
        console.error('[Jobs SSE] Error checking job status:', error);
        res.write(`event: error\ndata: ${JSON.stringify({
          message: 'Error checking job status',
        })}\n\n`);
        res.end();
        clearInterval(checkInterval);
      }
    }, 2000); // Check every 2 seconds

    // Clean up on client disconnect
    req.on('close', () => {
      clearInterval(checkInterval);
      console.log(`[Jobs SSE] Client disconnected from job ${jobId}`);
    });
  } catch (error) {
    clearInterval(checkInterval!);
    next(error);
  }
});

/**
 * DELETE /api/jobs/:jobId
 * Cancel a job
 */
router.delete('/:jobId', async (req, res, next) => {
  try {
    const { jobId } = req.params;

    const job = await analysisQueue.getJob(jobId);

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    const state = await job.getState();

    if (state === 'completed') {
      return res.status(400).json({ error: 'Cannot cancel completed job' });
    }

    await job.remove();

    res.json({ message: 'Job cancelled successfully', jobId });
  } catch (error) {
    next(error);
  }
});

export default router;
