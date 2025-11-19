import express from 'express';
import fs from 'fs';
import path from 'path';
import archiver from 'archiver';
import { ReportMetadata } from '../types';

const router = express.Router();
const REPORTS_DIR = '/app/reports';

/**
 * GET /api/reports
 * List all generated reports
 */
router.get('/', async (req, res, next) => {
  try {
    // Ensure reports directory exists
    if (!fs.existsSync(REPORTS_DIR)) {
      fs.mkdirSync(REPORTS_DIR, { recursive: true });
    }

    const reportDirs = fs.readdirSync(REPORTS_DIR);

    const reports: ReportMetadata[] = [];

    for (const dir of reportDirs) {
      const reportPath = path.join(REPORTS_DIR, dir);
      const stat = fs.statSync(reportPath);

      if (stat.isDirectory()) {
        // Parse directory name to extract metadata
        // Format: projectname-analysis-modelname-YYYYMMDD-HHMMSS
        const parts = dir.split('-');

        let projectName = 'Unknown Project';
        let model = 'unknown';

        if (parts.length >= 3) {
          // Find "analysis" index
          const analysisIndex = parts.indexOf('analysis');

          if (analysisIndex > 0) {
            projectName = parts.slice(0, analysisIndex).join('-');
            model = parts.slice(analysisIndex + 1).join('-');
          }
        }

        // Check if index.html exists (report is complete)
        const indexPath = path.join(reportPath, 'index.html');
        const status = fs.existsSync(indexPath) ? 'completed' : 'generating';

        reports.push({
          id: dir,
          projectName,
          model,
          createdAt: stat.mtime,
          status: status as any,
          path: reportPath,
        });
      }
    }

    // Sort by creation date (newest first)
    reports.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    res.json({
      reports,
      count: reports.length,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/reports/:reportId
 * Get specific report (serve index.html or download ZIP)
 */
router.get('/:reportId', async (req, res, next) => {
  try {
    const { reportId } = req.params;
    const { format = 'html' } = req.query;

    const reportPath = path.join(REPORTS_DIR, reportId);

    if (!fs.existsSync(reportPath)) {
      return res.status(404).json({ error: 'Report not found' });
    }

    if (format === 'zip') {
      // Stream report as ZIP file
      res.setHeader('Content-Type', 'application/zip');
      res.setHeader('Content-Disposition', `attachment; filename="${reportId}.zip"`);

      const archive = archiver('zip', { zlib: { level: 9 } });

      archive.on('error', (err) => {
        console.error('[Reports] Archive error:', err);
        next(err);
      });

      archive.pipe(res);
      archive.directory(reportPath, false);
      await archive.finalize();
    } else {
      // Serve index.html
      const indexPath = path.join(reportPath, 'index.html');

      if (!fs.existsSync(indexPath)) {
        return res.status(404).json({ error: 'Report not complete' });
      }

      res.sendFile(indexPath);
    }
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/reports/:reportId
 * Delete a report
 */
router.delete('/:reportId', async (req, res, next) => {
  try {
    const { reportId } = req.params;

    const reportPath = path.join(REPORTS_DIR, reportId);

    if (!fs.existsSync(reportPath)) {
      return res.status(404).json({ error: 'Report not found' });
    }

    // Delete report directory
    fs.rmSync(reportPath, { recursive: true, force: true });

    res.json({ message: 'Report deleted successfully', reportId });
  } catch (error) {
    next(error);
  }
});

export default router;
