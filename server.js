const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const axios = require('axios');
const pdfParse = require('pdf-parse');
const mammoth = require('mammoth');
const marked = require('marked');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8888;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static('public'));

// Ensure workspace directories exist
async function ensureWorkspace() {
  const dirs = [
    '/workspace/config',
    '/workspace/prompts',
    '/workspace/analysis',
    '/workspace/uploads'
  ];
  
  for (const dir of dirs) {
    await fs.mkdir(dir, { recursive: true });
  }
  
  // Initialize settings if not exists or empty
  const settingsPath = '/workspace/config/settings.json';
  let shouldCreateSettings = false;
  
  try {
    await fs.access(settingsPath);
    const stats = await fs.stat(settingsPath);
    if (stats.size === 0) {
      console.log('⚠️  settings.json exists but is empty, recreating...');
      shouldCreateSettings = true;
    }
  } catch {
    console.log('📝 settings.json not found, creating...');
    shouldCreateSettings = true;
  }
  
  if (shouldCreateSettings) {
    const settings = {
      theme: "dark",
      providers: {
        anthropic: {
          name: "Anthropic Claude",
          endpoint: "https://api.anthropic.com/v1/messages",
          models: ["claude-sonnet-4", "claude-opus-4", "claude-haiku-3"]
        },
        openai: {
          name: "OpenAI",
          endpoint: "https://api.openai.com/v1/chat/completions",
          models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        },
        openrouter: {
          name: "OpenRouter",
          endpoint: "https://openrouter.ai/api/v1/chat/completions",
          models: ["anthropic/claude-3-sonnet", "openai/gpt-4"]
        },
        google: {
          name: "Google Gemini",
          endpoint: "https://generativelanguage.googleapis.com/v1beta/models",
          models: ["gemini-1.5-pro", "gemini-1.5-flash"]
        },
        xai: {
          name: "xAI Grok",
          endpoint: "https://api.x.ai/v1/chat/completions",
          models: ["grok-beta"]
        },
        deepseek: {
          name: "DeepSeek",
          endpoint: "https://api.deepseek.com/v1/chat/completions",
          models: ["deepseek-chat", "deepseek-coder"]
        },
        mistral: {
          name: "Mistral AI",
          endpoint: "https://api.mistral.ai/v1/chat/completions",
          models: ["mistral-large", "mistral-medium"]
        },
        groq: {
          name: "Groq",
          endpoint: "https://api.groq.com/openai/v1/chat/completions",
          models: ["llama2-70b-4096", "mixtral-8x7b-32768"]
        }
      }
    };
    await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2));
    console.log('✅ settings.json created successfully');
  }
  
  // Initialize default prompt if not exists or empty
  const promptPath = '/workspace/prompts/default-prompt-v1.md';
  let shouldCreatePrompt = false;
  
  try {
    await fs.access(promptPath);
    const stats = await fs.stat(promptPath);
    if (stats.size === 0) {
      console.log('⚠️  default prompt exists but is empty, recreating...');
      shouldCreatePrompt = true;
    }
  } catch {
    console.log('📝 default prompt not found, creating...');
    shouldCreatePrompt = true;
  }
  
  if (shouldCreatePrompt) {
    const defaultPrompt = `# Product Viability Analysis Prompt v1

You are an AI Product Strategist analyzing product viability.

Create a comprehensive 9-tab HTML report covering:
1. Executive Summary
2. Market Landscape & Timing
3. Technical Feasibility
4. Competitive Advantage
5. Business Model & Economics
6. MVP Roadmap
7. Success Metrics & Risks
8. Go-to-Market Strategy
9. Provenance & Metadata

Use interactive visualizations and executive-style writing.`;
    await fs.writeFile(promptPath, defaultPrompt);
    console.log('✅ default prompt created successfully');
  }
  
  console.log('✅ Workspace initialization complete');
}

// File upload configuration
const storage = multer.diskStorage({
  destination: '/workspace/uploads',
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: parseInt(process.env.MAX_FILE_SIZE) || 5242880 },
  fileFilter: (req, file, cb) => {
    const allowed = ['.txt', '.md', '.pdf', '.docx'];
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, allowed.includes(ext));
  }
});

// Document text extraction
async function extractText(filepath) {
  const ext = path.extname(filepath).toLowerCase();
  const buffer = await fs.readFile(filepath);
  
  if (ext === '.pdf') {
    const data = await pdfParse(buffer);
    return data.text;
  } else if (ext === '.docx') {
    const result = await mammoth.extractRawText({ buffer });
    return result.value;
  } else if (ext === '.md') {
    return marked.parse(buffer.toString());
  } else {
    return buffer.toString('utf-8');
  }
}

// Routes

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/api/config', async (req, res) => {
  try {
    const settings = JSON.parse(await fs.readFile('/workspace/config/settings.json', 'utf-8'));
    const provider = process.env.MODEL_PROVIDER || 'anthropic';
    
    if (!settings.providers[provider]) {
      return res.status(400).json({ 
        error: `Unknown provider: ${provider}`,
        available: Object.keys(settings.providers)
      });
    }
    
    res.json({
      currentProvider: provider,
      defaultModel: process.env.DEFAULT_MODEL,
      hasApiKey: !!process.env.API_KEY,
      providers: settings.providers,
      theme: settings.theme
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/prompts', async (req, res) => {
  try {
    const files = await fs.readdir('/workspace/prompts');
    const prompts = await Promise.all(
      files
        .filter(f => f.endsWith('.md'))
        .map(async f => {
          const stats = await fs.stat(path.join('/workspace/prompts', f));
          return {
            filename: f,
            name: f.replace('.md', ''),
            modified: stats.mtime
          };
        })
    );
    res.json(prompts.sort((a, b) => b.modified - a.modified));
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/prompts/:filename', async (req, res) => {
  try {
    const content = await fs.readFile(
      path.join('/workspace/prompts', req.params.filename),
      'utf-8'
    );
    res.json({ content });
  } catch (error) {
    res.status(404).json({ error: 'Prompt not found' });
  }
});

app.post('/api/prompts', async (req, res) => {
  try {
    const { filename, content } = req.body;
    const filepath = path.join('/workspace/prompts', filename);
    await fs.writeFile(filepath, content);
    res.json({ success: true, filename });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/analysis', async (req, res) => {
  try {
    const files = await fs.readdir('/workspace/analysis');
    const analyses = await Promise.all(
      files
        .filter(f => f.endsWith('.html'))
        .map(async f => {
          const stats = await fs.stat(path.join('/workspace/analysis', f));
          return {
            filename: f,
            name: f.replace('.html', ''),
            created: stats.birthtime,
            size: stats.size
          };
        })
    );
    res.json(analyses.sort((a, b) => b.created - a.created));
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/analysis/:filename', async (req, res) => {
  try {
    const content = await fs.readFile(
      path.join('/workspace/analysis', req.params.filename),
      'utf-8'
    );
    res.send(content);
  } catch (error) {
    res.status(404).json({ error: 'Analysis not found' });
  }
});

app.delete('/api/analysis/:filename', async (req, res) => {
  try {
    await fs.unlink(path.join('/workspace/analysis', req.params.filename));
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }
    
    const text = await extractText(req.file.path);
    
    res.json({
      filename: req.file.filename,
      originalName: req.file.originalname,
      size: req.file.size,
      extractedText: text
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/analyze', async (req, res) => {
  try {
    const { promptContent, projectContent, projectName } = req.body;
    
    if (!process.env.API_KEY) {
      return res.status(400).json({ error: 'API_KEY not configured' });
    }
    
    const settings = JSON.parse(await fs.readFile('/workspace/config/settings.json', 'utf-8'));
    const provider = process.env.MODEL_PROVIDER || 'anthropic';
    const providerConfig = settings.providers[provider];
    
    // Prepare the analysis request
    const fullPrompt = `${promptContent}\n\n## Project to Analyze:\n\n${projectContent}`;
    
    // Call LLM API (implementation depends on provider)
    let response;
    
    if (provider === 'anthropic') {
      response = await axios.post(
        providerConfig.endpoint,
        {
          model: process.env.DEFAULT_MODEL || 'claude-sonnet-4',
          max_tokens: 16000,
          messages: [{ role: 'user', content: fullPrompt }]
        },
        {
          headers: {
            'x-api-key': process.env.API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
          }
        }
      );
      var analysisHtml = response.data.content[0].text;
    } else {
      // Generic OpenAI-compatible API
      response = await axios.post(
        providerConfig.endpoint,
        {
          model: process.env.DEFAULT_MODEL,
          messages: [{ role: 'user', content: fullPrompt }],
          max_tokens: 16000
        },
        {
          headers: {
            'Authorization': `Bearer ${process.env.API_KEY}`,
            'Content-Type': 'application/json'
          }
        }
      );
      var analysisHtml = response.data.choices[0].message.content;
    }
    
    // Save analysis
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${projectName.replace(/[^a-z0-9]/gi, '-')}-${timestamp}.html`;
    const filepath = path.join('/workspace/analysis', filename);
    
    await fs.writeFile(filepath, analysisHtml);
    
    res.json({ 
      success: true, 
      filename,
      preview: analysisHtml.substring(0, 500)
    });
    
  } catch (error) {
    console.error('Analysis error:', error.response?.data || error.message);
    res.status(500).json({ 
      error: error.response?.data?.error?.message || error.message 
    });
  }
});

// Start server
ensureWorkspace().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 VenturePulse running on http://localhost:${PORT}`);
    console.log(`📁 Workspace: /workspace`);
    console.log(`🔑 Provider: ${process.env.MODEL_PROVIDER || 'anthropic'}`);
  });
});
