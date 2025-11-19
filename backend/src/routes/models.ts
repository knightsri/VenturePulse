import express from 'express';
import { OpenRouterClient } from '../services/openrouter';

const router = express.Router();

/**
 * GET /api/models
 * Fetch available models from OpenRouter
 */
router.get('/', async (req, res, next) => {
  try {
    const models = await OpenRouterClient.fetchAvailableModels();

    res.json({
      models,
      count: models.length,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/models/clear-cache
 * Clear the models cache (admin endpoint)
 */
router.post('/clear-cache', (req, res) => {
  OpenRouterClient.clearCache();
  res.json({ message: 'Cache cleared successfully' });
});

export default router;
