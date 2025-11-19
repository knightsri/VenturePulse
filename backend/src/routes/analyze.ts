import express from 'express';
import multer from 'multer';
import { v4 as uuidv4 } from 'uuid';
import { analysisQueue } from '../services/queue';
import { FileProcessor } from '../services/fileProcessor';
import { AnalysisRequest, AnalysisResponse } from '../types';

const router = express.Router();

// Configure multer for file uploads
const upload = multer({
  dest: '/tmp/uploads/',
  limits: {
    fileSize: (parseInt(process.env.MAX_UPLOAD_SIZE_MB || '10')) * 1024 * 1024,
  },
  fileFilter: (req, file, cb) => {
    if (FileProcessor.isValidFileType(file.mimetype, file.originalname)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Supported: .txt, .md, .docx, .pdf'));
    }
  },
});

/**
 * POST /api/analyze
 * Submit a project for analysis
 */
router.post('/', upload.single('file'), async (req, res, next) => {
  try {
    const { projectName, projectContent, models: modelsStr } = req.body;
    const file = req.file;

    // Validation
    if (!projectName) {
      return res.status(400).json({ error: 'Project name is required' });
    }

    if (!modelsStr) {
      return res.status(400).json({ error: 'At least one model must be selected' });
    }

    let models: string[];
    try {
      models = JSON.parse(modelsStr);
    } catch {
      return res.status(400).json({ error: 'Invalid models format' });
    }

    if (!Array.isArray(models) || models.length === 0) {
      return res.status(400).json({ error: 'At least one model must be selected' });
    }

    // Extract project content from file or body
    let content = projectContent;

    if (file) {
      console.log(`[Analyze] Processing uploaded file: ${file.originalname}`);
      content = await FileProcessor.extractText(file.path, file.mimetype);

      // Clean up uploaded file
      const fs = await import('fs');
      fs.unlinkSync(file.path);
    }

    if (!content) {
      return res.status(400).json({ error: 'Project content or file is required' });
    }

    // Validate content length
    const contentValidation = FileProcessor.isValidContentLength(content);
    if (!contentValidation.valid) {
      return res.status(400).json({ error: contentValidation.message });
    }

    console.log(`[Analyze] Creating analysis jobs for project: ${projectName}`);
    console.log(`[Analyze] Models: ${models.join(', ')}`);
    console.log(`[Analyze] Content length: ${content.length} characters`);

    // Create a job for each selected model
    const jobIds: string[] = [];

    for (const model of models) {
      const jobId = uuidv4();

      await analysisQueue.add({
        jobId,
        projectName,
        projectContent: content,
        model,
      }, {
        jobId,
      });

      jobIds.push(jobId);
      console.log(`[Analyze] Created job ${jobId} for model ${model}`);
    }

    const response: AnalysisResponse = {
      jobIds,
      message: `Created ${jobIds.length} analysis job(s)`,
    };

    res.json(response);
  } catch (error) {
    console.error('[Analyze] Error:', error);
    next(error);
  }
});

export default router;
