import express from 'express';
import prisma from '../utils/database';

const router = express.Router();

/**
 * GET /api/ideas
 * List all ideas with optional filtering and searching
 */
router.get('/', async (req, res, next) => {
  try {
    const { search, status, industry, limit = '50', offset = '0' } = req.query;

    const where: any = {};

    // Add search filter
    if (search) {
      where.OR = [
        { name: { contains: search as string, mode: 'insensitive' } },
        { description: { contains: search as string, mode: 'insensitive' } },
      ];
    }

    // Add status filter
    if (status) {
      where.status = status;
    }

    // Add industry filter
    if (industry) {
      where.industry = industry;
    }

    const [ideas, total] = await Promise.all([
      prisma.idea.findMany({
        where,
        include: {
          reports: {
            select: {
              id: true,
              status: true,
              createdAt: true,
            },
          },
          _count: {
            select: {
              reports: true,
              versions: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        take: parseInt(limit as string),
        skip: parseInt(offset as string),
      }),
      prisma.idea.count({ where }),
    ]);

    res.json({
      ideas,
      total,
      limit: parseInt(limit as string),
      offset: parseInt(offset as string),
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/ideas/:ideaId
 * Get a specific idea with all details
 */
router.get('/:ideaId', async (req, res, next) => {
  try {
    const { ideaId } = req.params;

    const idea = await prisma.idea.findUnique({
      where: { id: ideaId },
      include: {
        versions: {
          orderBy: { createdAt: 'desc' },
        },
        reports: {
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (!idea) {
      return res.status(404).json({ error: 'Idea not found' });
    }

    res.json(idea);
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/ideas
 * Create a new idea
 */
router.post('/', async (req, res, next) => {
  try {
    const {
      name,
      description,
      industry,
      targetMarket,
      estimatedBudget,
      tags,
      notes,
      status,
    } = req.body;

    // Validation
    if (!name || !description) {
      return res.status(400).json({ error: 'Name and description are required' });
    }

    if (description.length < 100) {
      return res.status(400).json({ error: 'Description must be at least 100 characters' });
    }

    const idea = await prisma.idea.create({
      data: {
        name,
        description,
        industry,
        targetMarket,
        estimatedBudget: estimatedBudget ? parseFloat(estimatedBudget) : null,
        tags: tags || [],
        notes,
        status: status || 'DRAFT',
      },
    });

    // Create initial version
    await prisma.ideaVersion.create({
      data: {
        ideaId: idea.id,
        version: 1,
        name,
        description,
        industry,
        targetMarket,
        estimatedBudget: estimatedBudget ? parseFloat(estimatedBudget) : null,
        tags: tags || [],
        notes,
        versionNotes: 'Initial version',
      },
    });

    res.status(201).json(idea);
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /api/ideas/:ideaId
 * Update an idea (creates a new version)
 */
router.put('/:ideaId', async (req, res, next) => {
  try {
    const { ideaId } = req.params;
    const {
      name,
      description,
      industry,
      targetMarket,
      estimatedBudget,
      tags,
      notes,
      status,
      versionNotes,
    } = req.body;

    const existingIdea = await prisma.idea.findUnique({
      where: { id: ideaId },
      include: {
        versions: {
          orderBy: { version: 'desc' },
          take: 1,
        },
      },
    });

    if (!existingIdea) {
      return res.status(404).json({ error: 'Idea not found' });
    }

    // Update idea
    const idea = await prisma.idea.update({
      where: { id: ideaId },
      data: {
        name,
        description,
        industry,
        targetMarket,
        estimatedBudget: estimatedBudget ? parseFloat(estimatedBudget) : null,
        tags: tags || [],
        notes,
        status,
      },
    });

    // Create new version
    const newVersion = (existingIdea.versions[0]?.version || 0) + 1;
    await prisma.ideaVersion.create({
      data: {
        ideaId: idea.id,
        version: newVersion,
        name,
        description,
        industry,
        targetMarket,
        estimatedBudget: estimatedBudget ? parseFloat(estimatedBudget) : null,
        tags: tags || [],
        notes,
        versionNotes: versionNotes || `Version ${newVersion}`,
      },
    });

    res.json(idea);
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/ideas/:ideaId
 * Delete an idea
 */
router.delete('/:ideaId', async (req, res, next) => {
  try {
    const { ideaId } = req.params;

    await prisma.idea.delete({
      where: { id: ideaId },
    });

    res.json({ message: 'Idea deleted successfully' });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/ideas/:ideaId/analyze
 * Start analysis from a saved idea
 */
router.post('/:ideaId/analyze', async (req, res, next) => {
  try {
    const { ideaId } = req.params;
    const { models } = req.body;

    if (!models || models.length === 0) {
      return res.status(400).json({ error: 'At least one model is required' });
    }

    const idea = await prisma.idea.findUnique({
      where: { id: ideaId },
    });

    if (!idea) {
      return res.status(404).json({ error: 'Idea not found' });
    }

    // Update idea status
    await prisma.idea.update({
      where: { id: ideaId },
      data: { status: 'ANALYZING' },
    });

    // Import analysis queue
    const { analysisQueue } = await import('../services/queue');
    const { v4: uuidv4 } = await import('uuid');

    const jobIds: string[] = [];

    for (const model of models) {
      const jobId = uuidv4();

      await analysisQueue.add({
        jobId,
        projectName: idea.name,
        projectContent: idea.description,
        model,
        ideaId: idea.id,
      }, {
        jobId,
      });

      jobIds.push(jobId);
    }

    res.json({
      jobIds,
      message: `Created ${jobIds.length} analysis job(s)`,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/ideas/:ideaId/reports
 * Get all reports for an idea
 */
router.get('/:ideaId/reports', async (req, res, next) => {
  try {
    const { ideaId } = req.params;

    const reports = await prisma.report.findMany({
      where: { ideaId },
      orderBy: { createdAt: 'desc' },
    });

    res.json({ reports });
  } catch (error) {
    next(error);
  }
});

export default router;
