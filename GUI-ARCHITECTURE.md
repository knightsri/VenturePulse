# VenturePulse GUI - Architecture Design

## Overview

Transform VenturePulse from CLI-only to a modern web application with Docker containerization, enabling non-technical users to generate product viability reports through an intuitive interface.

---

## Architecture Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: Tailwind CSS + shadcn/ui components
- **State Management**: React Context API + React Query for server state
- **File Upload**: react-dropzone
- **Progress Tracking**: Server-Sent Events (SSE) or WebSockets
- **PWA Support**: next-pwa for service worker, manifest, offline functionality
- **Mobile Optimization**: Responsive design, touch gestures, install prompts

### Backend
- **Runtime**: Node.js 20 (LTS)
- **Framework**: Express.js
- **API Layer**: RESTful + SSE for real-time updates
- **File Processing**:
  - `.txt`, `.md` - Direct text extraction
  - `.docx` - mammoth.js
  - `.pdf` - pdf-parse
- **Job Queue**: Bull (Redis-backed) for async report generation
- **Storage**: Volume-mounted file system for reports

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Services**:
  - `venturepulse-web` - Next.js frontend (port 3000)
  - `venturepulse-api` - Express backend (port 4000)
  - `venturepulse-worker` - Report generation worker
  - `redis` - Job queue + session storage
- **Reverse Proxy**: Nginx (optional, for production)

### External Dependencies
- **OpenRouter API** - LLM provider (existing)
- **Environment Variables**: `.env` file (Docker secrets in production)

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │         Next.js Frontend (Port 3000)               │     │
│  │  - Project input form                              │     │
│  │  - Model selection (multi-select)                  │     │
│  │  - Real-time progress display                      │     │
│  │  - Report viewer/download                          │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/SSE
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Docker Compose Network                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Express API (Port 4000)                           │   │
│  │    - File upload endpoint                            │   │
│  │    - Job creation & status endpoints                 │   │
│  │    - SSE progress stream                             │   │
│  │    - Report retrieval API                            │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Redis (Port 6379)                            │   │
│  │         - Job queue (Bull)                           │   │
│  │         - Session storage                            │   │
│  │         - Progress tracking                          │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Worker Process (venturepulse-worker)              │   │
│  │    - Consumes jobs from queue                        │   │
│  │    - Executes analyze-script.sh                      │   │
│  │    - Updates progress in Redis                       │   │
│  │    - Stores reports in shared volume                 │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼ (External API Call)
         ┌────────────────────────────┐
         │   OpenRouter API           │
         │   - LLM model access       │
         └────────────────────────────┘
```

---

## Core Features

### 1. Project Input
**Options**:
- **File Upload**: Drag & drop or click to upload (`.txt`, `.md`, `.docx`, `.pdf`)
- **Text Area**: Paste project description directly
- **File Size Limit**: 10MB max
- **Validation**: Minimum 100 characters required

**UI Components**:
- File upload zone with progress indicator
- Rich text area with character count
- Preview pane showing parsed content

### 2. Model Selection
**Feature**: Multi-select model chooser

**Model List** (fetched from OpenRouter API on load):
- Display: Model name, provider, cost estimate, speed rating
- Categorization:
  - Free Models
  - Budget Models (<$0.50 per analysis)
  - Balanced Models ($0.50-$2)
  - Premium Models (>$2)
- Search/Filter: By provider, cost, speed
- Default Selection: `google/gemini-2.0-flash-exp:free`

**API Integration**:
```javascript
// Fetch available models from OpenRouter
GET https://openrouter.ai/api/v1/models
// Cache for 24 hours, refresh daily
```

**Cost Estimation**:
- Real-time calculation: `(input_tokens + output_tokens) × model_price`
- Display total cost for selected models
- Warning if total >$10

### 3. Report Generation

**Workflow**:
1. User submits form → Upload file + selected models
2. Backend creates job(s) in Redis queue (one per model)
3. Worker picks up job, executes analysis
4. Progress updates stream via SSE
5. Completed reports stored in `/reports` volume
6. User redirected to results page

**Progress Tracking** (Real-time via SSE):
```
Job ID: abc123-model1
Status: in_progress
Section: 3/9 (Technical Feasibility)
Elapsed: 2m 34s
Estimated remaining: 7m 15s
```

**Multi-Model Parallel Processing**:
- Each model gets separate job
- Worker pool processes jobs concurrently (configurable: 1-5 workers)
- UI shows progress for all models simultaneously

### 4. Report Viewing & Management

**Results Dashboard**:
- Grid/list view of all generated reports
- Filter by: Date, project name, model, status
- Sort by: Created date, model, status
- Actions: View, Download, Delete, Share

**Report Viewer**:
- Embedded iframe viewer (reuse existing index.html wrapper)
- Section navigation sidebar
- Download options:
  - Individual sections (HTML)
  - Full report (ZIP)
  - PDF export (optional, via Puppeteer)
- Share link generation (public URL, optional)

**Storage Management**:
- Display storage usage
- Auto-cleanup: Delete reports older than 30 days (configurable)
- User can download before deletion

### 5. Ideas Library (Save & Manage Project Ideas)

**Purpose**: Allow users to save project ideas, manage them over time, and reuse them for multiple analyses.

**Ideas Library Page** (`/ideas`):
- Grid/list view of all saved ideas
- Search by name, description, tags
- Filter by: Status (draft, analyzed, archived), Industry, Tags, Date range
- Sort by: Recent, Name, Last analyzed, # of analyses
- Quick actions per idea: View, Edit, Analyze, Delete
- New Idea button
- Export/Import ideas (JSON format)

**Idea Card**:
- Project name and description preview
- Industry tag, custom tags
- Status badge (draft, analyzing, analyzed, archived)
- Metadata: Created date, last analyzed date
- Number of linked analyses
- Quick action buttons

**New Idea Form**:
- Project name* (required)
- Industry dropdown (Tech, Healthcare, Fintech, E-commerce, etc.)
- Target market (B2B, B2C, B2B2C)
- Estimated budget
- Description* (required, min 100 chars, or file upload)
- Tags (multi-select with autocomplete + custom)
- Notes (optional)
- Actions: Save as Draft, Save and Analyze

**Idea Detail Page** (`/ideas/:ideaId`):
- **Overview Tab**:
  - Full idea details with metadata
  - Version history (track changes over time)
  - Attachments (uploaded files)
- **Analyses Tab**:
  - List all analyses for this idea (model, date, verdict, score, cost)
  - Compare button if 2+ analyses exist
  - Empty state with "Analyze Now" CTA
- **Edit Tab**:
  - Edit form (creates new version on save)
  - Version notes field

**Enhanced Analyze Flow**:
- Option to select saved idea OR create new
- If saved idea selected: Auto-populate description, link report to idea
- If new: Optional "Save to library" checkbox
- Both flows converge to model selection

**Data Storage**:
- PostgreSQL for persistent storage
- IndexedDB for offline PWA access
- Sync between server and local storage

### 6. Multi-Model Comparison

**Purpose**: When user analyzes the same idea with 2+ models, generate a comparison view showing differences, consensus, and recommendations.

**Comparison Dashboard** (`/compare/:ideaId` or `/compare?reports=id1,id2,id3`):

**Viability Score Comparison**:
- Show overall score for each model
- Progress bars with verdict badges
- Highlight score spread (if >1.5 points, show warning)
- Visual disagreement indicator

**Dimension Breakdown Table**:
| Dimension | Model 1 | Model 2 | Model 3 | Average | Spread |
|-----------|---------|---------|---------|---------|--------|
| Market    | 8.0     | 8.5     | 6.5     | 7.7     | 2.0 ⚠️ |
| Technical | 7.5     | 8.0     | 7.0     | 7.5     | 1.0 ✓  |
| Compete   | 6.5     | 7.5     | 5.5     | 6.5     | 2.0 ⚠️ |
| Business  | 7.5     | 8.5     | 6.0     | 7.3     | 2.5 ⚠️ |
| Execution | 7.5     | 8.0     | 7.0     | 7.5     | 1.0 ✓  |

**Color Coding**:
- Green (<1.0): Consensus
- Yellow (1.0-2.0): Moderate disagreement
- Red (>2.0): High disagreement

**Analysis Insights**:
- **Cost vs Quality**: Compare cost and scores per model
- **Consensus Areas**: Where models agree (spread <1.0)
- **Disagreement Areas**: Where models differ significantly (spread >2.0)
- **Recommendation**: Which model to trust, areas to validate

**Visualizations**:
- Radar chart: 5 dimensions with all models overlaid
- Cost vs Quality scatter plot: X=cost, Y=score
- Section-by-section table comparison (verdict, highlights, risks)

**Auto-Trigger**:
- When user submits with 2+ models, auto-generate comparison on completion
- Show "Compare Analyses" button on Idea detail page if 2+ reports exist
- Dashboard indicates ideas with multiple analyses

**Advanced Features** (P2):
- AI-powered meta-analysis (explains why models disagree)
- Detailed section-by-section comparison
- Shareable comparison links
- Export comparison as PDF

---

## API Endpoints

### POST `/api/analyze`
**Description**: Submit project for analysis

**Request**:
```json
{
  "projectName": "SmartPlate",
  "projectContent": "...",
  "models": [
    "anthropic/claude-sonnet-4.5",
    "google/gemini-2.0-flash-exp:free"
  ]
}
```

**Response**:
```json
{
  "jobIds": [
    "abc123-claude",
    "abc123-gemini"
  ],
  "message": "Analysis jobs created"
}
```

### GET `/api/jobs/:jobId`
**Description**: Get job status

**Response**:
```json
{
  "jobId": "abc123-claude",
  "status": "in_progress",
  "progress": {
    "currentSection": 3,
    "totalSections": 9,
    "sectionName": "Technical Feasibility",
    "percentage": 33
  },
  "startedAt": "2024-01-20T10:30:00Z",
  "estimatedCompletion": "2024-01-20T10:45:00Z"
}
```

### GET `/api/jobs/:jobId/stream`
**Description**: SSE endpoint for real-time progress

**Stream Format**:
```
event: progress
data: {"section": 3, "total": 9, "name": "Technical Feasibility"}

event: complete
data: {"reportPath": "/reports/abc123-claude"}

event: error
data: {"message": "API rate limit exceeded"}
```

### GET `/api/reports`
**Description**: List all generated reports

**Response**:
```json
{
  "reports": [
    {
      "id": "abc123-claude",
      "projectName": "SmartPlate",
      "model": "anthropic/claude-sonnet-4.5",
      "createdAt": "2024-01-20T10:30:00Z",
      "status": "completed",
      "path": "/reports/smartplate-analysis-claude-sonnet-4-5-20240120-103000"
    }
  ]
}
```

### GET `/api/reports/:reportId`
**Description**: Download report (ZIP or HTML)

**Response**: Binary file stream

### DELETE `/api/reports/:reportId`
**Description**: Delete report

### GET `/api/models`
**Description**: List available OpenRouter models with metadata

**Response**:
```json
{
  "models": [
    {
      "id": "anthropic/claude-sonnet-4.5",
      "name": "Claude Sonnet 4.5",
      "provider": "Anthropic",
      "pricing": {
        "prompt": 0.003,
        "completion": 0.015
      },
      "estimatedCost": 4.50,
      "speed": "medium",
      "recommended": true
    }
  ]
}
```

### Ideas Management API

**POST `/api/ideas`** - Create new idea
**GET `/api/ideas`** - List all ideas (with pagination, search, filters)
**GET `/api/ideas/:ideaId`** - Get idea details
**PUT `/api/ideas/:ideaId`** - Update idea (creates new version)
**DELETE `/api/ideas/:ideaId`** - Delete idea
**GET `/api/ideas/:ideaId/reports`** - Get all reports for this idea
**POST `/api/ideas/:ideaId/analyze`** - Start analysis from saved idea
**GET `/api/ideas/export`** - Export all ideas as JSON
**POST `/api/ideas/import`** - Import ideas from JSON file

### Multi-Model Comparison API

**GET `/api/ideas/:ideaId/comparison`** - Get comparison of all reports for this idea
**GET `/api/compare?reports=id1,id2,id3`** - Get comparison of specific reports
**POST `/api/comparison/:comparisonId/meta-analysis`** - Generate AI meta-analysis (optional)
**GET `/api/comparison/:comparisonId/export`** - Export comparison as PDF/HTML

---

## UI/UX Design

### Page Structure

**1. Home Page** (`/`)
- Hero section: "AI-Powered Product Viability Analysis"
- Feature highlights
- CTA: "Start Analysis" → navigates to `/analyze`
- Recent reports preview
- Pricing/cost calculator

**2. Analyze Page** (`/analyze`)
- **Step 1**: Project Input
  - File upload or text area
  - Character count: min 100, recommended 500-2000
- **Step 2**: Model Selection
  - Grid of model cards (logo, name, cost, speed)
  - Multi-select with cost total
  - Recommendation badge on best free/paid models
- **Step 3**: Review & Submit
  - Preview project content
  - Confirm selected models
  - Estimated cost & time
  - Submit button

**3. Progress Page** (`/progress/:jobId`)
- Real-time progress tracker for each model
- Section-by-section status (pending, in_progress, completed, failed)
- Elapsed time & estimated completion
- Live log stream (optional, collapsible)
- Cancel job button

**4. Results Page** (`/results/:reportId`)
- Report viewer with iframe
- Section navigation sidebar
- Download buttons (HTML, ZIP, PDF)
- Share link generation
- Regenerate section option

**5. Dashboard Page** (`/dashboard`)
- All generated reports (table/grid view)
- Filters: Date, model, project name, status
- Bulk actions: Download, delete
- Storage usage indicator

**6. Ideas Library Page** (`/ideas`)
- Grid/list view of saved ideas
- Search bar and advanced filters
- Sort options (recent, name, last analyzed)
- New Idea button
- Quick actions per idea (View, Edit, Analyze, Delete)

**7. Idea Detail Page** (`/ideas/:ideaId`)
- Tab navigation (Overview, Analyses, Edit)
- Overview: Full details, version history, attachments
- Analyses: List all reports, compare button if 2+
- Edit: Update form, creates new version

**8. Comparison Page** (`/compare/:ideaId` or `/compare?reports=...`)
- Viability score comparison with progress bars
- Dimension breakdown table (color-coded by spread)
- Analysis insights (consensus, disagreement, recommendation)
- Visualizations (radar chart, cost vs quality)
- Export comparison button

### Component Library

**shadcn/ui Components**:
- `Button`, `Card`, `Input`, `Textarea`
- `Select`, `Checkbox`, `Progress`
- `Table`, `Dialog`, `Tabs`
- `Alert`, `Badge`, `Skeleton`
- `Dropdown Menu`, `Toast`

**Custom Components**:
- `FileUpload` - Drag & drop with preview
- `ModelSelector` - Multi-select grid with filtering
- `ProgressTracker` - Real-time job progress
- `ReportViewer` - Iframe wrapper with controls
- `CostEstimator` - Dynamic pricing calculator
- `IdeaCard` - Idea preview card with metadata and actions
- `IdeaForm` - Reusable form for create/edit idea
- `IdeaFilters` - Advanced search and filtering
- `ComparisonChart` - Radar chart for multi-model scores
- `DimensionBreakdown` - Color-coded table of score spreads

---

## Docker Configuration

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:4000
    depends_on:
      - api
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "4000:4000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - REDIS_URL=redis://redis:6379
      - NODE_ENV=development
    depends_on:
      - redis
    volumes:
      - ./backend:/app
      - /app/node_modules
      - reports-volume:/app/reports
      - ./prompts:/app/prompts:ro
      - ./scripts:/app/scripts:ro

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - REDIS_URL=redis://redis:6379
      - NODE_ENV=development
    depends_on:
      - redis
    volumes:
      - reports-volume:/app/reports
      - ./prompts:/app/prompts:ro
      - ./scripts:/app/scripts:ro

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  reports-volume:
  redis-data:
```

### Frontend Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

### Backend Dockerfile

```dockerfile
FROM node:20-alpine

# Install bash for shell scripts
RUN apk add --no-cache bash curl jq

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 4000

CMD ["npm", "start"]
```

### Worker Dockerfile

```dockerfile
FROM node:20-alpine

# Install bash, curl, jq for analyze-script.sh
RUN apk add --no-cache bash curl jq

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Copy VenturePulse scripts
COPY scripts /app/scripts
COPY prompts /app/prompts

RUN chmod +x /app/scripts/*.sh

CMD ["node", "worker.js"]
```

---

## Launcher Scripts

### `run.sh` (Linux/Mac)

```bash
#!/bin/bash

echo "🎯 Starting VenturePulse GUI..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OPENROUTER_API_KEY"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start containers
echo "🔨 Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ VenturePulse is running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API:      http://localhost:4000"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo ""
```

### `run.bat` (Windows)

```batch
@echo off
echo 🎯 Starting VenturePulse GUI...

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Copying from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env and add your OPENROUTER_API_KEY
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Build and start containers
echo 🔨 Building containers...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

echo.
echo ✅ VenturePulse is running!
echo.
echo 📱 Frontend: http://localhost:3000
echo 🔌 API:      http://localhost:4000
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo.
```

---

## Environment Variables

### `.env.example`

```bash
# OpenRouter API Key (REQUIRED)
OPENROUTER_API_KEY=your_api_key_here

# Application Settings
NODE_ENV=development
PORT=4000

# Redis Configuration
REDIS_URL=redis://redis:6379

# Worker Configuration
WORKER_CONCURRENCY=3

# Report Storage
REPORTS_RETENTION_DAYS=30
MAX_UPLOAD_SIZE_MB=10

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

---

## File Structure

```
VenturePulse/
├── docker-compose.yml
├── .env.example
├── .env
├── run.sh
├── run.bat
│
├── frontend/                      # Next.js application
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Home page
│   │   ├── analyze/
│   │   │   └── page.tsx          # Analysis form
│   │   ├── progress/
│   │   │   └── [jobId]/
│   │   │       └── page.tsx      # Progress tracker
│   │   ├── results/
│   │   │   └── [reportId]/
│   │   │       └── page.tsx      # Report viewer
│   │   └── dashboard/
│   │       └── page.tsx          # All reports
│   ├── components/
│   │   ├── ui/                   # shadcn components
│   │   ├── FileUpload.tsx
│   │   ├── ModelSelector.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── ReportViewer.tsx
│   │   └── CostEstimator.tsx
│   ├── lib/
│   │   ├── api.ts                # API client
│   │   └── utils.ts
│   └── public/
│
├── backend/                       # Express API
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── server.ts             # Express app
│   │   ├── routes/
│   │   │   ├── analyze.ts
│   │   │   ├── jobs.ts
│   │   │   ├── reports.ts
│   │   │   └── models.ts
│   │   ├── services/
│   │   │   ├── queue.ts          # Bull queue setup
│   │   │   ├── openrouter.ts    # OpenRouter API client
│   │   │   └── fileProcessor.ts # File parsing
│   │   ├── workers/
│   │   │   └── reportWorker.ts  # Job processor
│   │   └── utils/
│   │       ├── logger.ts
│   │       └── validation.ts
│   └── worker.js                 # Worker entry point
│
├── prompts/                       # Existing prompt files
│   ├── common-instructions.md
│   └── sections/
│
├── scripts/                       # Existing shell scripts
│   ├── analyze-script.sh
│   ├── call-openrouter.sh
│   ├── create-wrapper.sh
│   └── generate-provenance.sh
│
└── examples/                      # Keep existing examples
```

---

## Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/VenturePulse.git
cd VenturePulse

# 2. Copy environment file
cp .env.example .env

# 3. Add your OpenRouter API key to .env
# OPENROUTER_API_KEY=sk-or-v1-...

# 4. Run the application
./run.sh          # Linux/Mac
run.bat           # Windows

# 5. Open browser
# http://localhost:3000
```

### Development Mode

```bash
# Start all services
docker-compose up

# Watch logs
docker-compose logs -f

# Restart specific service
docker-compose restart api

# Rebuild after code changes
docker-compose up --build

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start with production config
docker-compose -f docker-compose.prod.yml up -d

# Use nginx for reverse proxy
# Configure SSL with Let's Encrypt
```

---

## Security Considerations

1. **API Key Protection**: Never commit `.env` file; use Docker secrets in production
2. **File Upload Validation**: Whitelist extensions, scan for malware, limit size
3. **Rate Limiting**: Implement per-user rate limits (10 analyses/day for free tier)
4. **Authentication** (Phase 2): Add user accounts with JWT or NextAuth.js
5. **CORS**: Restrict to known frontend origins
6. **Input Sanitization**: Validate all user inputs, escape HTML in reports
7. **Report Access Control**: Generate unique IDs, optionally require authentication

---

## Performance Optimizations

1. **Caching**: Cache OpenRouter model list for 24 hours
2. **CDN**: Serve static assets (reports) via CDN
3. **Database** (optional): Add PostgreSQL for report metadata instead of filesystem scanning
4. **Worker Scaling**: Increase worker count based on queue depth
5. **SSE Connection Pooling**: Limit concurrent SSE connections per user
6. **Report Compression**: gzip reports before download

---

## Future Enhancements

### Phase 2
- User authentication & accounts
- Report history & versioning
- Custom prompt templates
- Collaborative reports (sharing with teams)
- Webhook notifications
- Slack/Discord integration

### Phase 3
- AI chat interface for follow-up questions
- Comparative report mode (compare multiple ideas)
- Export to PowerPoint/PDF
- Notion/Confluence integration
- White-label deployment option

---

## Testing Strategy

### Unit Tests
- API endpoints (Jest + Supertest)
- Worker job processing
- File upload validation
- Cost calculation logic

### Integration Tests
- End-to-end analysis workflow
- SSE progress streaming
- Multi-model parallel processing

### E2E Tests
- Playwright for frontend flows
- User journey: Upload → Select models → View results

---

---

## PWA (Progressive Web App) Implementation

### Overview

Transform VenturePulse into a fully installable Progressive Web App with offline capabilities, push notifications, and native-like mobile experience.

### PWA Features

**Core Capabilities:**
- **Installable**: Add to home screen on iOS/Android
- **Offline Support**: View previously generated reports without internet
- **Background Sync**: Queue analyses when offline, sync when online
- **Push Notifications**: Notify when report generation completes
- **App-like Experience**: Full-screen mode, no browser chrome
- **Fast Loading**: Service worker caching for instant startup

### Configuration Files

#### `next.config.js` (with next-pwa)

```javascript
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/localhost:4000\/api\/reports.*/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'venturepulse-reports',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        },
      },
    },
    {
      urlPattern: /^https:\/\/localhost:4000\/api\/models/i,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'venturepulse-models',
        expiration: {
          maxEntries: 10,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        },
      },
    },
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'venturepulse-images',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
        },
      },
    },
  ],
});

module.exports = withPWA({
  reactStrictMode: true,
  swcMinify: true,
});
```

#### `public/manifest.json`

```json
{
  "name": "VenturePulse - AI Product Analysis",
  "short_name": "VenturePulse",
  "description": "AI-powered product viability analysis in minutes",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#667eea",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "New Analysis",
      "short_name": "New",
      "description": "Start a new product analysis",
      "url": "/analyze",
      "icons": [
        {
          "src": "/icons/shortcut-new.png",
          "sizes": "96x96"
        }
      ]
    },
    {
      "name": "Dashboard",
      "short_name": "Dashboard",
      "description": "View all reports",
      "url": "/dashboard",
      "icons": [
        {
          "src": "/icons/shortcut-dashboard.png",
          "sizes": "96x96"
        }
      ]
    }
  ],
  "categories": ["business", "productivity", "utilities"],
  "screenshots": [
    {
      "src": "/screenshots/analyze.png",
      "sizes": "540x720",
      "type": "image/png"
    },
    {
      "src": "/screenshots/progress.png",
      "sizes": "540x720",
      "type": "image/png"
    },
    {
      "src": "/screenshots/report.png",
      "sizes": "540x720",
      "type": "image/png"
    }
  ]
}
```

#### `frontend/app/layout.tsx` (PWA Metadata)

```typescript
import type { Metadata, Viewport } from 'next';

export const metadata: Metadata = {
  title: 'VenturePulse - AI Product Analysis',
  description: 'AI-powered product viability analysis in minutes',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'VenturePulse',
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: '/icons/icon-192x192.png',
    apple: '/icons/icon-192x192.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#667eea',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};
```

### Mobile Optimization

#### Touch-Friendly UI Components

**Button Sizes:**
- Minimum touch target: 44x44px (iOS) / 48x48px (Android)
- Spacing between touch targets: 8px minimum

**Gestures:**
- Swipe to delete reports
- Pull to refresh on dashboard
- Pinch to zoom on report viewer
- Long-press for context menu

**Responsive Breakpoints:**
```css
/* tailwind.config.js */
theme: {
  screens: {
    'xs': '375px',   // iPhone SE
    'sm': '640px',   // Small tablets
    'md': '768px',   // Tablets
    'lg': '1024px',  // Laptops
    'xl': '1280px',  // Desktops
    '2xl': '1536px', // Large desktops
  }
}
```

#### Mobile-Optimized Pages

**Home Page (Mobile):**
- Simplified hero with single CTA
- Vertical card layout
- Larger fonts (16px minimum)
- Thumb-friendly navigation at bottom

**Analyze Page (Mobile):**
- One-column layout
- Large file upload area (full-width)
- Model cards in single column
- Sticky submit button at bottom
- Collapsible sections to save space

**Progress Page (Mobile):**
- Full-screen progress display
- Large status indicators
- Swipe to cancel (with confirmation)
- Haptic feedback on completion (iOS)

**Report Viewer (Mobile):**
- Bottom sheet navigation
- Swipe between sections
- Floating action button for download
- Share via native share API

**Dashboard (Mobile):**
- Card view (not table)
- Infinite scroll (no pagination)
- Swipe-to-delete
- Floating action button for new analysis

### Install Prompt

#### `frontend/components/InstallPrompt.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Download, X } from 'lucide-react';

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showInstall, setShowInstall] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Check if iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    setIsIOS(iOS);

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return; // Already installed
    }

    // Check if dismissed recently
    const dismissed = localStorage.getItem('install-prompt-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed);
      const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) {
        return; // Don't show for 7 days after dismissal
      }
    }

    // Listen for beforeinstallprompt (Android/Desktop)
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Show iOS instructions after 3 seconds
    if (iOS) {
      setTimeout(() => setShowInstall(true), 3000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      setDeferredPrompt(null);
      setShowInstall(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('install-prompt-dismissed', Date.now().toString());
    setShowInstall(false);
  };

  if (!showInstall) return null;

  return (
    <Alert className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 shadow-lg">
      <Download className="h-4 w-4" />
      <AlertDescription className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {isIOS ? (
            <div>
              <p className="font-semibold mb-1">Install VenturePulse</p>
              <p className="text-sm text-muted-foreground">
                Tap <span className="inline-block">⎙</span> then "Add to Home Screen"
              </p>
            </div>
          ) : (
            <div>
              <p className="font-semibold mb-1">Install VenturePulse</p>
              <p className="text-sm text-muted-foreground">
                Install for offline access and faster loading
              </p>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          {!isIOS && deferredPrompt && (
            <Button size="sm" onClick={handleInstallClick}>
              Install
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={handleDismiss}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
}
```

### Offline Functionality

#### Service Worker Strategy

**Caching Strategy by Resource Type:**

1. **Static Assets** (HTML, CSS, JS, images):
   - Strategy: Cache First
   - Duration: 1 year
   - Update: On service worker update

2. **API - Models List**:
   - Strategy: Stale While Revalidate
   - Duration: 24 hours
   - Fallback: Cached version

3. **API - Reports**:
   - Strategy: Cache First
   - Duration: 30 days
   - Fallback: Offline message

4. **API - Analysis Submission**:
   - Strategy: Network First
   - Fallback: Queue for background sync
   - User notification: "Will submit when online"

#### Background Sync for Offline Analysis

```typescript
// frontend/lib/backgroundSync.ts

export async function queueAnalysisForSync(analysisData: AnalysisRequest) {
  if ('serviceWorker' in navigator && 'sync' in window.registration) {
    // Store in IndexedDB
    await storeOfflineAnalysis(analysisData);

    // Register sync event
    await navigator.serviceWorker.ready.then((registration) => {
      return registration.sync.register('sync-analyses');
    });

    return { queued: true, message: 'Will submit when online' };
  }

  throw new Error('Offline submission not supported');
}

// Service worker listens for sync event
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-analyses') {
    event.waitUntil(syncPendingAnalyses());
  }
});

async function syncPendingAnalyses() {
  const pending = await getPendingAnalyses();

  for (const analysis of pending) {
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: JSON.stringify(analysis),
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        await removeFromPendingQueue(analysis.id);
      }
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }
}
```

### Push Notifications

#### Backend - Send Notification on Completion

```typescript
// backend/src/services/pushNotifications.ts

import webpush from 'web-push';

webpush.setVapidDetails(
  'mailto:support@venturepulse.com',
  process.env.VAPID_PUBLIC_KEY!,
  process.env.VAPID_PRIVATE_KEY!
);

export async function sendReportCompleteNotification(
  subscription: PushSubscription,
  reportData: { projectName: string; reportId: string }
) {
  const payload = JSON.stringify({
    title: 'Report Ready! 🎯',
    body: `${reportData.projectName} analysis is complete`,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    data: {
      url: `/results/${reportData.reportId}`,
    },
  });

  try {
    await webpush.sendNotification(subscription, payload);
  } catch (error) {
    console.error('Push notification failed:', error);
  }
}
```

#### Frontend - Subscribe to Push

```typescript
// frontend/lib/notifications.ts

export async function subscribeToPushNotifications() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    throw new Error('Push notifications not supported');
  }

  const registration = await navigator.serviceWorker.ready;

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(
      process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!
    ),
  });

  // Send subscription to backend
  await fetch('/api/notifications/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription),
  });

  return subscription;
}
```

#### Service Worker - Handle Push Events

```javascript
// public/sw.js

self.addEventListener('push', (event) => {
  const data = event.data.json();

  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    vibrate: [200, 100, 200],
    data: data.data,
    actions: [
      {
        action: 'view',
        title: 'View Report',
      },
      {
        action: 'close',
        title: 'Dismiss',
      },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  }
});
```

### Mobile-Specific Features

#### Native Share API

```typescript
// frontend/components/ShareButton.tsx

export function ShareButton({ reportId, projectName }: ShareButtonProps) {
  const handleShare = async () => {
    const shareData = {
      title: `${projectName} - VenturePulse Analysis`,
      text: 'Check out this product viability analysis',
      url: `${window.location.origin}/results/${reportId}`,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        // User cancelled or error occurred
      }
    } else {
      // Fallback to copy link
      await navigator.clipboard.writeText(shareData.url);
      toast.success('Link copied to clipboard');
    }
  };

  return (
    <Button onClick={handleShare}>
      <Share2 className="mr-2 h-4 w-4" />
      Share Report
    </Button>
  );
}
```

#### Haptic Feedback (iOS)

```typescript
// frontend/lib/haptics.ts

export function triggerHaptic(type: 'light' | 'medium' | 'heavy' = 'light') {
  if ('vibrate' in navigator) {
    const patterns = {
      light: [10],
      medium: [20],
      heavy: [30],
    };
    navigator.vibrate(patterns[type]);
  }
}

// Usage: On report completion, delete action, etc.
triggerHaptic('medium');
```

#### Pull-to-Refresh

```typescript
// frontend/app/dashboard/page.tsx

'use client';

import { useEffect, useRef } from 'react';
import { usePullToRefresh } from '@/hooks/usePullToRefresh';

export default function DashboardPage() {
  const { refetch } = useReports();

  usePullToRefresh({
    onRefresh: async () => {
      await refetch();
      triggerHaptic('light');
    },
  });

  return <div>...</div>;
}
```

### App Icons & Splash Screens

**Required Icon Sizes:**
- 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

**iOS Splash Screens** (Apple Touch Icons):
```html
<!-- In app/layout.tsx head -->
<link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon.png" />
<link rel="apple-touch-startup-image" href="/splash/iphone5_splash.png" media="(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)" />
<link rel="apple-touch-startup-image" href="/splash/iphone6_splash.png" media="(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)" />
<!-- Add more sizes for different devices -->
```

### Performance Optimizations for Mobile

**Image Optimization:**
```typescript
import Image from 'next/image';

<Image
  src="/hero.png"
  alt="VenturePulse"
  width={800}
  height={600}
  priority // For above-the-fold images
  placeholder="blur" // For better perceived performance
/>
```

**Code Splitting:**
```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic';

const ReportViewer = dynamic(() => import('@/components/ReportViewer'), {
  loading: () => <ReportViewerSkeleton />,
  ssr: false, // Don't render on server
});
```

**Font Optimization:**
```typescript
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap', // Prevent FOIT (Flash of Invisible Text)
  preload: true,
});
```

### Testing PWA

**Installation Test:**
- [ ] Test install on Android Chrome
- [ ] Test install on iOS Safari
- [ ] Test install on Desktop Chrome/Edge
- [ ] Verify app icons appear correctly
- [ ] Test splash screen on iOS

**Offline Test:**
- [ ] Disconnect network
- [ ] Navigate to installed app
- [ ] View previously loaded reports
- [ ] Try to submit new analysis (should queue)
- [ ] Reconnect and verify sync

**Push Notification Test:**
- [ ] Subscribe to push notifications
- [ ] Submit analysis
- [ ] Wait for completion
- [ ] Verify notification received
- [ ] Click notification to open report

**Mobile Performance Test:**
- [ ] Lighthouse PWA score >90
- [ ] Time to interactive <3s on 3G
- [ ] First contentful paint <1.5s
- [ ] Total bundle size <500KB

### PWA Deployment Checklist

- [ ] Generate all required icon sizes
- [ ] Create splash screens for iOS
- [ ] Configure VAPID keys for push notifications
- [ ] Test service worker registration
- [ ] Verify manifest.json is served correctly
- [ ] Enable HTTPS (required for PWA)
- [ ] Test on multiple devices and browsers
- [ ] Submit to Google Play Store (optional, via TWA)
- [ ] Submit to Apple App Store (optional, via wrapper)

---

This architecture provides a solid foundation for transforming VenturePulse into a production-ready SaaS application with full PWA capabilities, maintaining the core analysis quality while delivering a native app-like experience on mobile devices.
