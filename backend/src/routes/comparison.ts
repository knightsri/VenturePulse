import express from 'express';
import { ComparisonEngine } from '../services/comparisonEngine';
import prisma from '../utils/database';

const router = express.Router();

/**
 * GET /api/compare?reports=id1,id2,id3
 * Generate comparison for specific report IDs
 */
router.get('/', async (req, res, next) => {
  try {
    const { reports } = req.query;

    if (!reports || typeof reports !== 'string') {
      return res.status(400).json({
        error: 'Missing or invalid reports parameter. Expected comma-separated report IDs.',
      });
    }

    const reportIds = reports.split(',').map((id) => id.trim());

    if (reportIds.length < 2) {
      return res.status(400).json({
        error: 'At least 2 report IDs are required for comparison.',
      });
    }

    const comparison = await ComparisonEngine.generateComparison(reportIds);

    res.json({
      success: true,
      comparison,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/compare/idea/:ideaId
 * Generate comparison for all reports of a specific idea
 */
router.get('/idea/:ideaId', async (req, res, next) => {
  try {
    const { ideaId } = req.params;

    // Fetch all completed reports for this idea
    const reports = await prisma.report.findMany({
      where: {
        ideaId,
        status: 'COMPLETED',
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    if (reports.length < 2) {
      return res.status(400).json({
        error: `Not enough completed reports for this idea. Found ${reports.length}, need at least 2.`,
      });
    }

    const reportIds = reports.map((r) => r.id);
    const comparison = await ComparisonEngine.generateComparison(reportIds);

    res.json({
      success: true,
      comparison,
      totalReports: reports.length,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/compare/latest?projectName=MyProject
 * Compare the latest reports for a given project name
 */
router.get('/latest', async (req, res, next) => {
  try {
    const { projectName } = req.query;

    if (!projectName || typeof projectName !== 'string') {
      return res.status(400).json({
        error: 'Missing or invalid projectName parameter.',
      });
    }

    // Get the latest completed reports for this project name
    const reports = await prisma.report.findMany({
      where: {
        projectName,
        status: 'COMPLETED',
      },
      orderBy: {
        createdAt: 'desc',
      },
      distinct: ['model'],
    });

    if (reports.length < 2) {
      return res.status(400).json({
        error: `Not enough completed reports for project "${projectName}". Found ${reports.length}, need at least 2.`,
      });
    }

    const reportIds = reports.map((r) => r.id);
    const comparison = await ComparisonEngine.generateComparison(reportIds);

    res.json({
      success: true,
      comparison,
      totalReports: reports.length,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
