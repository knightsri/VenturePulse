# VenturePulse GUI - Complete Task List

**Project Goal**: Transform VenturePulse from CLI-only to a full-featured web application with Docker containerization.

**Estimated Effort**: 20-30 hours
**Complexity**: Medium-High
**Prerequisites**: Node.js 20, Docker Desktop, OpenRouter API key

---

## Phase 1: Project Setup & Infrastructure (2-3 hours)

### TASK-001: Initialize Project Structure
- [ ] Create `frontend/` directory for Next.js application
- [ ] Create `backend/` directory for Express API
- [ ] Move existing `prompts/` and `scripts/` to root (keep accessible to both)
- [ ] Update `.gitignore` for new structure:
  - Add `node_modules/`, `.next/`, `dist/`, `reports/`
  - Add `.env` (keep `.env.example`)
  - Add `docker-compose.override.yml`
- [ ] Create `docker-compose.yml` at root
- [ ] Create `.env.example` with all required variables
- [ ] Create `run.sh` and `run.bat` launcher scripts
- [ ] Make `run.sh` executable: `chmod +x run.sh`

### TASK-002: Frontend - Next.js Initialization
- [ ] `cd frontend && npx create-next-app@latest . --typescript --tailwind --app --no-src-dir`
- [ ] Install dependencies:
  ```bash
  npm install @tanstack/react-query axios react-dropzone
  npm install lucide-react class-variance-authority clsx tailwind-merge
  npm install @radix-ui/react-dialog @radix-ui/react-select @radix-ui/react-progress
  npm install date-fns recharts
  ```
- [ ] Install shadcn/ui CLI: `npx shadcn-ui@latest init`
- [ ] Add shadcn components:
  ```bash
  npx shadcn-ui@latest add button card input textarea select
  npx shadcn-ui@latest add progress table dialog tabs badge
  npx shadcn-ui@latest add alert dropdown-menu toast skeleton
  ```
- [ ] Create `frontend/Dockerfile`
- [ ] Configure `next.config.js` for API proxy
- [ ] Update `tailwind.config.js` with custom theme colors

### TASK-003: Backend - Express API Initialization
- [ ] `cd backend && npm init -y`
- [ ] Install dependencies:
  ```bash
  npm install express cors dotenv bull redis
  npm install multer express-validator morgan helmet
  npm install mammoth pdf-parse axios
  npm install --save-dev typescript @types/node @types/express
  npm install --save-dev ts-node nodemon
  ```
- [ ] Create `backend/tsconfig.json`
- [ ] Create `backend/Dockerfile`
- [ ] Create `backend/Dockerfile.worker`
- [ ] Create `backend/src/server.ts` (Express app skeleton)
- [ ] Create `backend/worker.js` (Bull worker skeleton)
- [ ] Add npm scripts to `package.json`:
  ```json
  {
    "scripts": {
      "dev": "nodemon --exec ts-node src/server.ts",
      "build": "tsc",
      "start": "node dist/server.js",
      "worker": "node worker.js"
    }
  }
  ```

### TASK-004: Docker Configuration
- [ ] Create `docker-compose.yml` with 4 services:
  - `web` (Next.js frontend)
  - `api` (Express backend)
  - `worker` (Report generation worker)
  - `redis` (Job queue)
- [ ] Configure volume mounts:
  - `reports-volume` for shared report storage
  - `redis-data` for persistence
  - Bind mount `prompts/` and `scripts/` as read-only
- [ ] Configure environment variable passing from host to containers
- [ ] Test Docker build: `docker-compose build`
- [ ] Test Docker startup: `docker-compose up`
- [ ] Verify all services are healthy

### TASK-005: Environment Configuration
- [ ] Create `.env.example` with all variables:
  ```
  OPENROUTER_API_KEY=your_key_here
  NODE_ENV=development
  PORT=4000
  REDIS_URL=redis://redis:6379
  WORKER_CONCURRENCY=3
  REPORTS_RETENTION_DAYS=30
  MAX_UPLOAD_SIZE_MB=10
  FRONTEND_URL=http://localhost:3000
  ```
- [ ] Document environment setup in README
- [ ] Create validation script to check required env vars

---

## Phase 2: Backend API Development (6-8 hours)

### TASK-101: Redis & Bull Queue Setup
- [ ] Create `backend/src/services/queue.ts`:
  - Initialize Bull queue connection
  - Export `analysisQueue` instance
  - Configure retry logic (3 retries, exponential backoff)
- [ ] Create job types interface:
  ```typescript
  interface AnalysisJob {
    jobId: string;
    projectName: string;
    projectContent: string;
    model: string;
    userId?: string;
  }
  ```
- [ ] Implement queue event listeners (completed, failed, progress)
- [ ] Test queue connectivity

### TASK-102: File Upload & Processing
- [ ] Create `backend/src/services/fileProcessor.ts`
- [ ] Implement text extraction for:
  - `.txt` - Direct read
  - `.md` - Direct read
  - `.docx` - Use mammoth.js
  - `.pdf` - Use pdf-parse
- [ ] Add file validation:
  - Whitelist extensions
  - Max size check (10MB)
  - Minimum content length (100 chars)
- [ ] Add error handling for corrupt files
- [ ] Create unit tests for each file type

### TASK-103: OpenRouter API Client
- [ ] Create `backend/src/services/openrouter.ts`
- [ ] Implement `fetchAvailableModels()`:
  - Call `GET https://openrouter.ai/api/v1/models`
  - Parse and filter relevant models
  - Calculate cost estimates
  - Cache results (24 hours)
- [ ] Implement `estimateAnalysisCost(model, projectLength)`:
  - Calculate input tokens (~1500 + project length)
  - Estimate output tokens (~8000 per section × 9 sections)
  - Return cost estimate per model
- [ ] Add error handling for API failures
- [ ] Test with real API key

### TASK-104: Report Generation Service
- [ ] Create `backend/src/services/reportGenerator.ts`
- [ ] Implement `generateReport(job: AnalysisJob)`:
  - Create temp directory for project file
  - Write project content to `.md` file
  - Execute `analyze-script.sh` with model parameter
  - Capture stdout/stderr
  - Monitor progress (parse script output)
  - Move generated report to `/reports` volume
  - Return report path
- [ ] Implement progress tracking:
  - Parse "Section X/9" from script output
  - Update job progress in Redis
  - Emit progress events
- [ ] Add error handling:
  - Script execution failures
  - OpenRouter API errors
  - Timeout handling (30 min max)
- [ ] Implement cleanup on failure

### TASK-105: API Routes - Analysis Submission
- [ ] Create `backend/src/routes/analyze.ts`
- [ ] Implement `POST /api/analyze`:
  - Validate request body (projectName, projectContent, models[])
  - Validate file upload if present
  - Process uploaded file → extract text
  - For each selected model:
    - Generate unique jobId
    - Create job in Bull queue
    - Return jobId
  - Return array of jobIds
- [ ] Add request validation with express-validator
- [ ] Add rate limiting (optional)
- [ ] Test endpoint with Postman/curl

### TASK-106: API Routes - Job Status
- [ ] Create `backend/src/routes/jobs.ts`
- [ ] Implement `GET /api/jobs/:jobId`:
  - Fetch job from Bull queue
  - Return status (waiting, active, completed, failed)
  - Return progress data
  - Return error if failed
  - Calculate estimated completion time
- [ ] Implement `GET /api/jobs/:jobId/stream` (SSE):
  - Create Server-Sent Events endpoint
  - Stream progress updates in real-time
  - Listen to Redis pub/sub for updates
  - Close connection on completion or error
- [ ] Implement `DELETE /api/jobs/:jobId`:
  - Cancel active job
  - Remove from queue
  - Clean up temp files
- [ ] Test SSE endpoint with curl

### TASK-107: API Routes - Reports Management
- [ ] Create `backend/src/routes/reports.ts`
- [ ] Implement `GET /api/reports`:
  - Scan `/reports` directory
  - Parse directory names (extract project, model, timestamp)
  - Return metadata array (id, projectName, model, createdAt, status)
  - Add pagination (limit/offset)
  - Add filtering (by project, model, date range)
  - Add sorting (by date, model)
- [ ] Implement `GET /api/reports/:reportId`:
  - Validate reportId
  - Check if report directory exists
  - Serve `index.html` or ZIP file
  - Add download headers
- [ ] Implement `GET /api/reports/:reportId/sections/:sectionId`:
  - Serve individual section HTML
- [ ] Implement `DELETE /api/reports/:reportId`:
  - Validate reportId
  - Delete report directory
  - Return confirmation
- [ ] Add access control (optional, for Phase 2)

### TASK-108: API Routes - Models Endpoint
- [ ] Create `backend/src/routes/models.ts`
- [ ] Implement `GET /api/models`:
  - Fetch from OpenRouter API (with caching)
  - Categorize models (free, budget, balanced, premium)
  - Add metadata (speed rating, quality score, recommended flag)
  - Return structured JSON
- [ ] Add cache invalidation endpoint (admin only)
- [ ] Test with frontend integration

### TASK-109: Worker Implementation
- [ ] Create `backend/src/workers/reportWorker.ts`
- [ ] Implement job processor:
  - Listen for jobs from `analysisQueue`
  - Execute report generation for each job
  - Update progress in Redis
  - Publish progress events to Redis pub/sub
  - Handle completion (save report path to job result)
  - Handle failures (save error, retry if applicable)
- [ ] Add logging (Winston or Pino)
- [ ] Implement graceful shutdown
- [ ] Test worker with multiple concurrent jobs

### TASK-110: Error Handling & Logging
- [ ] Create `backend/src/utils/logger.ts` (Winston)
- [ ] Add structured logging throughout API
- [ ] Create error handler middleware
- [ ] Add request logging (Morgan)
- [ ] Implement health check endpoint `GET /health`
- [ ] Add monitoring endpoints (queue stats, worker status)

---

## Phase 3: Frontend Development (8-10 hours)

### TASK-201: API Client Setup
- [ ] Create `frontend/lib/api.ts`
- [ ] Implement API client using axios:
  - Base URL from env var
  - Request/response interceptors
  - Error handling
- [ ] Create API functions:
  - `submitAnalysis(data)`
  - `getJobStatus(jobId)`
  - `streamJobProgress(jobId, onProgress)`
  - `getReports(filters?)`
  - `getReport(reportId)`
  - `deleteReport(reportId)`
  - `getModels()`
- [ ] Setup React Query provider in `app/layout.tsx`

### TASK-202: Home Page
- [ ] Create `frontend/app/page.tsx`
- [ ] Design hero section:
  - Headline: "AI-Powered Product Viability Analysis"
  - Subheading: "Transform weeks of research into comprehensive reports in 15 minutes"
  - CTA button: "Start Analysis" → `/analyze`
- [ ] Add feature highlights section (3 columns):
  - Comprehensive Analysis (9 dimensions)
  - Multi-Model Support (compare analyses)
  - Professional Reports (investor-ready)
- [ ] Add recent reports preview (if any exist)
- [ ] Add cost calculator widget
- [ ] Make responsive (mobile-first)

### TASK-203: Analyze Page - Project Input
- [ ] Create `frontend/app/analyze/page.tsx`
- [ ] Create `frontend/components/FileUpload.tsx`:
  - Implement drag & drop (react-dropzone)
  - Show file preview
  - Display file info (name, size, type)
  - Validate file type (.txt, .md, .docx, .pdf)
  - Show upload progress
  - Error states (invalid file, too large)
- [ ] Create text area alternative:
  - Rich text input (plain textarea for MVP)
  - Character count display
  - Minimum 100 chars validation
  - Recommended 500-2000 chars guidance
- [ ] Add toggle to switch between file upload and text area
- [ ] Implement file content extraction on frontend (optional, or send to backend)

### TASK-204: Analyze Page - Model Selection
- [ ] Create `frontend/components/ModelSelector.tsx`
- [ ] Fetch models from API on mount (with loading skeleton)
- [ ] Display models in grid layout:
  - Model card: Logo, name, provider, cost, speed rating
  - Category badges (Free, Budget, Balanced, Premium)
  - Recommended badge for top models
- [ ] Implement multi-select functionality:
  - Checkbox per model
  - Selected count indicator
  - Select all / deselect all
- [ ] Add search/filter:
  - Search by name
  - Filter by category
  - Filter by provider
- [ ] Show total cost estimate at bottom
- [ ] Add warning if total cost >$10
- [ ] Default selection: free model

### TASK-205: Analyze Page - Review & Submit
- [ ] Add review step (expandable section or separate tab):
  - Preview project content (truncated)
  - List selected models with costs
  - Total estimated cost
  - Estimated time (10-15 min × number of models)
- [ ] Implement submit button:
  - Validate form (project content + at least one model)
  - Show loading state during submission
  - Submit to API
  - Handle errors (display toast)
  - On success: Navigate to progress page with jobIds
- [ ] Add form state management (React Hook Form or useState)
- [ ] Add validation feedback (inline errors)

### TASK-206: Progress Page
- [ ] Create `frontend/app/progress/[jobId]/page.tsx`
- [ ] Create `frontend/components/ProgressTracker.tsx`:
  - Display job status (waiting, in_progress, completed, failed)
  - Show section progress (3/9 Technical Feasibility)
  - Progress bar with percentage
  - Elapsed time
  - Estimated completion time
  - Live log stream (optional, collapsible)
- [ ] Implement SSE connection:
  - Connect to `/api/jobs/:jobId/stream`
  - Listen for progress events
  - Update UI in real-time
  - Handle connection errors/reconnection
  - Close connection on completion
- [ ] Handle multiple jobs (if multiple models):
  - Show progress for each model in separate cards
  - Overall progress aggregation
- [ ] Add cancel button:
  - Call DELETE endpoint
  - Confirm before canceling
  - Redirect to dashboard on cancel
- [ ] On completion:
  - Show success message
  - Provide link to view report
  - Auto-redirect after 3 seconds (optional)
- [ ] On failure:
  - Show error message
  - Provide retry button
  - Link to support/troubleshooting

### TASK-207: Results Page
- [ ] Create `frontend/app/results/[reportId]/page.tsx`
- [ ] Create `frontend/components/ReportViewer.tsx`:
  - Embed report in iframe
  - Load `index.html` from report directory
  - Handle iframe communication (optional)
- [ ] Add section navigation sidebar (if not using existing report wrapper):
  - List all 9 sections
  - Highlight current section
  - Click to navigate to section
- [ ] Add action buttons:
  - Download HTML (single section or full report)
  - Download ZIP (all sections)
  - Download PDF (optional, Phase 2)
  - Share link (copy to clipboard)
  - Regenerate section (optional, Phase 2)
- [ ] Add metadata display:
  - Project name
  - Model used
  - Generated date
  - Total cost (if available)
- [ ] Make responsive (hide sidebar on mobile, show as dropdown)

### TASK-208: Dashboard Page
- [ ] Create `frontend/app/dashboard/page.tsx`
- [ ] Fetch all reports from API
- [ ] Display reports in table view:
  - Columns: Project Name, Model, Status, Created Date, Actions
  - Row actions: View, Download, Delete
  - Sortable columns
  - Pagination (20 per page)
- [ ] Add alternative grid view (toggle button)
- [ ] Implement filters:
  - Date range picker
  - Model selector (dropdown)
  - Project name search
  - Status filter (completed, failed, in_progress)
- [ ] Implement delete action:
  - Confirm dialog before delete
  - Optimistic update (remove from UI immediately)
  - Show toast on success/error
- [ ] Add bulk actions (optional):
  - Select multiple reports
  - Bulk download
  - Bulk delete
- [ ] Show storage usage indicator
- [ ] Add "New Analysis" button → `/analyze`

### TASK-209: Cost Estimator Component
- [ ] Create `frontend/components/CostEstimator.tsx`
- [ ] Calculate cost in real-time:
  - Based on project length (char count)
  - Selected models
  - Estimated tokens (input + output)
- [ ] Display breakdown:
  - Cost per model
  - Total cost
  - Estimated time
- [ ] Add comparison mode (optional):
  - "This analysis will cost $4.50 vs. $150 for a consultant"

### TASK-210: UI Polish & Responsiveness
- [ ] Ensure all pages are mobile-responsive
- [ ] Add loading skeletons for async data
- [ ] Implement toast notifications (success, error, info)
- [ ] Add dark mode support (optional, using next-themes)
- [ ] Add animations (Framer Motion, optional)
- [ ] Optimize images (Next.js Image component)
- [ ] Add meta tags for SEO
- [ ] Test on Chrome, Firefox, Safari
- [ ] Test on mobile devices (iOS, Android)

---

## Phase 4: Integration & Testing (3-4 hours)

### TASK-301: End-to-End Integration Testing
- [ ] Test complete flow:
  1. Upload project file on `/analyze`
  2. Select multiple models
  3. Submit analysis
  4. Monitor progress on `/progress/:jobId`
  5. View completed report on `/results/:reportId`
  6. Download report
  7. Verify report quality (all 9 sections generated)
- [ ] Test with different file types (.txt, .md, .docx, .pdf)
- [ ] Test with different models (free, premium)
- [ ] Test error scenarios:
  - Invalid API key
  - File too large
  - Unsupported file type
  - API timeout
  - Worker crash recovery

### TASK-302: Multi-Model Testing
- [ ] Submit analysis with 3+ models simultaneously
- [ ] Verify parallel processing works
- [ ] Check Redis queue handling
- [ ] Verify worker concurrency (3 workers processing in parallel)
- [ ] Check for race conditions
- [ ] Verify all reports generated correctly

### TASK-303: Performance Testing
- [ ] Test with large project files (5MB+)
- [ ] Test with 10+ concurrent analyses
- [ ] Monitor Docker resource usage (CPU, RAM)
- [ ] Optimize slow endpoints (profile with Chrome DevTools)
- [ ] Add loading states for slow operations
- [ ] Test SSE connection stability over 15+ minutes

### TASK-304: Error Handling & Edge Cases
- [ ] Test missing environment variables
- [ ] Test invalid OpenRouter API key
- [ ] Test Redis connection failure
- [ ] Test worker crash during analysis
- [ ] Test file upload limits (exactly 10MB)
- [ ] Test with empty project content
- [ ] Test with special characters in project name
- [ ] Test browser back button during analysis
- [ ] Test multiple browser tabs with same job

### TASK-305: Docker & Deployment Testing
- [ ] Test fresh Docker build (no cache): `docker-compose build --no-cache`
- [ ] Test production build: `docker-compose -f docker-compose.prod.yml up`
- [ ] Test volume persistence (restart containers, verify reports still exist)
- [ ] Test environment variable override
- [ ] Test `run.sh` and `run.bat` scripts on different platforms
- [ ] Document any platform-specific issues (WSL, Mac M1, etc.)

---

## Phase 5: Documentation & Polish (2-3 hours)

### TASK-401: Update README.md
- [ ] Add GUI section to README with:
  - Prerequisites (Docker, Node.js, API key)
  - Quick start guide (using `run.sh`/`run.bat`)
  - Screenshots of UI
  - Architecture overview
  - Development setup
  - Troubleshooting guide
- [ ] Add comparison: CLI vs. GUI
- [ ] Update installation instructions
- [ ] Add demo GIF/video (optional)

### TASK-402: Create User Guide
- [ ] Create `docs/USER-GUIDE.md`:
  - Getting started walkthrough
  - How to create an analysis
  - How to select models
  - Understanding the reports
  - Downloading and sharing
  - FAQ
- [ ] Add screenshots for each major step
- [ ] Include troubleshooting section

### TASK-403: Create Developer Guide
- [ ] Create `docs/DEVELOPER-GUIDE.md`:
  - Architecture overview
  - Tech stack explanation
  - How to add new features
  - How to modify prompts
  - How to add new section types
  - API documentation
  - Testing guide
- [ ] Document Docker setup in detail
- [ ] Explain worker queue system
- [ ] Include API endpoint reference

### TASK-404: Add Inline Code Documentation
- [ ] Add JSDoc comments to all API functions
- [ ] Add component prop documentation (TypeScript interfaces)
- [ ] Document complex algorithms
- [ ] Add README.md in each major directory (frontend/, backend/)

### TASK-405: Create Demo Content
- [ ] Add 2-3 example project files in `examples/`:
  - Simple project (500 words)
  - Complex project (2000 words)
  - Edge case project (unusual domain)
- [ ] Generate sample reports for each
- [ ] Include in repository (so users can test immediately)

---

## Phase 6: PWA (Progressive Web App) Implementation (3-4 hours)

### TASK-601: PWA Configuration Setup
- [ ] Install next-pwa: `npm install next-pwa`
- [ ] Configure `next.config.js` with PWA settings:
  - Set up service worker destination
  - Configure runtime caching strategies
  - Disable PWA in development mode
- [ ] Create `public/manifest.json`:
  - App name, short name, description
  - Start URL and display mode
  - Theme colors (brand purple #667eea)
  - Icon definitions (8 sizes)
  - App shortcuts (New Analysis, Dashboard)
  - Categories and screenshots
- [ ] Update `frontend/app/layout.tsx` with PWA metadata:
  - Add manifest link
  - Configure Apple Web App settings
  - Set viewport and theme color
- [ ] Test manifest.json loads correctly

### TASK-602: App Icons & Visual Assets
- [ ] Generate all required icon sizes:
  - 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512
  - Use maskable format for Android
- [ ] Create app icons in `public/icons/`:
  - VenturePulse logo with brand colors
  - Shortcut icons (new analysis, dashboard)
  - Badge icon for notifications
- [ ] Create iOS-specific assets:
  - Apple touch icon (180x180)
  - Splash screens for different iOS devices
- [ ] Create Android-specific assets:
  - Adaptive icons
  - Monochrome icons for dynamic theming
- [ ] Test icons appear correctly on install

### TASK-603: Service Worker & Offline Support
- [ ] Verify service worker auto-generation by next-pwa
- [ ] Configure caching strategies in `next.config.js`:
  - Cache reports (CacheFirst, 30 days)
  - Cache models list (StaleWhileRevalidate, 24 hours)
  - Cache images (CacheFirst, 1 year)
- [ ] Create `frontend/lib/serviceWorker.ts` helpers:
  - Service worker registration check
  - Update notification
  - Offline detection
- [ ] Implement offline indicator in UI:
  - Banner showing "You're offline"
  - Disable submit button when offline
  - Queue indicator for pending submissions
- [ ] Test offline functionality:
  - Load app while online
  - Go offline
  - Navigate between pages
  - View cached reports
  - Verify graceful degradation

### TASK-604: Background Sync for Offline Submissions
- [ ] Create `frontend/lib/backgroundSync.ts`:
  - IndexedDB storage for offline analyses
  - Queue management functions
  - Sync registration
- [ ] Implement background sync in service worker:
  - Listen for 'sync' events
  - Fetch pending analyses from IndexedDB
  - Submit to API when online
  - Remove from queue on success
- [ ] Update analyze form to handle offline submissions:
  - Detect offline state
  - Store in IndexedDB
  - Register sync event
  - Show "Queued for submission" message
- [ ] Create pending analyses UI:
  - Dashboard section showing queued analyses
  - Status: "Waiting for network"
  - Option to cancel queued submission
- [ ] Test background sync:
  - Submit analysis while offline
  - Verify stored in IndexedDB
  - Come online
  - Verify auto-submission
  - Check job appears in progress page

### TASK-605: Install Prompt Component
- [ ] Create `frontend/components/InstallPrompt.tsx`:
  - Detect `beforeinstallprompt` event (Android/Desktop)
  - Detect iOS Safari (show instructions)
  - Check if already installed
  - Check if recently dismissed (7-day cooldown)
- [ ] Implement install UI:
  - Alert/banner at bottom of page
  - "Install" button (Android/Desktop)
  - iOS instructions (Share → Add to Home Screen)
  - Dismiss button
- [ ] Add install prompt logic:
  - Show after 3 seconds on homepage
  - Don't show if already installed
  - Don't show if dismissed recently
  - Store dismissal in localStorage
- [ ] Add to `app/layout.tsx`
- [ ] Test on multiple platforms:
  - Android Chrome (install button)
  - iOS Safari (instructions)
  - Desktop Chrome (install button)
  - Verify dismissal works

### TASK-606: Push Notifications
- [ ] Generate VAPID keys for web push:
  ```bash
  npx web-push generate-vapid-keys
  ```
- [ ] Add VAPID keys to `.env`:
  - VAPID_PUBLIC_KEY
  - VAPID_PRIVATE_KEY
- [ ] Install backend dependency: `npm install web-push`
- [ ] Create `backend/src/services/pushNotifications.ts`:
  - Configure web-push with VAPID keys
  - Implement `sendReportCompleteNotification()`
  - Store user subscriptions (in-memory Map or Redis)
- [ ] Create API endpoint `POST /api/notifications/subscribe`:
  - Accept push subscription from client
  - Store subscription with user/session ID
  - Return success
- [ ] Create `frontend/lib/notifications.ts`:
  - Check if push supported
  - Request permission
  - Subscribe to push manager
  - Send subscription to backend
- [ ] Add notification permission UI:
  - Prompt on first analysis submission
  - "Get notified when report is ready"
  - Allow/Don't Allow buttons
- [ ] Implement push in worker:
  - On job completion, fetch user subscription
  - Send push notification with report details
- [ ] Handle push events in service worker:
  - Show notification with title, body, icon
  - Add action buttons (View Report, Dismiss)
  - Handle notification click → open report
- [ ] Test push notifications:
  - Subscribe on frontend
  - Submit analysis
  - Wait for completion
  - Verify notification received
  - Click to open report

### TASK-607: Mobile Optimization
- [ ] Update `tailwind.config.js` with mobile breakpoints:
  - xs: 375px (iPhone SE)
  - sm: 640px
  - md: 768px
  - lg: 1024px
  - xl: 1280px
  - 2xl: 1536px
- [ ] Ensure all buttons meet touch target sizes:
  - Minimum 44x44px (iOS) / 48x48px (Android)
  - 8px spacing between targets
- [ ] Implement mobile-specific UI:
  - Bottom sheet navigation for reports (mobile)
  - Floating action buttons (sticky at bottom)
  - Larger form inputs (16px font to prevent zoom)
  - Simplified navigation for small screens
- [ ] Add touch gestures:
  - Swipe to delete reports (optional)
  - Pull to refresh on dashboard
- [ ] Test on real devices:
  - iPhone (Safari)
  - Android (Chrome)
  - iPad (Safari)
  - Verify no horizontal scroll
  - Verify all interactive elements are tappable

### TASK-608: Mobile-Specific Features
- [ ] Implement Native Share API:
  - Create `frontend/components/ShareButton.tsx`
  - Detect if `navigator.share` available
  - Share report URL with title and text
  - Fallback to copy link if not supported
- [ ] Add haptic feedback:
  - Create `frontend/lib/haptics.ts`
  - Trigger on important actions (completion, delete, error)
  - Use `navigator.vibrate()` API
- [ ] Implement pull-to-refresh:
  - Create `frontend/hooks/usePullToRefresh.ts`
  - Add to dashboard page
  - Show refresh indicator
  - Trigger refetch on pull
- [ ] Add home screen shortcuts:
  - Already defined in manifest.json
  - Test shortcuts work on install
- [ ] Test all mobile features:
  - Share button opens native share sheet
  - Haptic feedback on supported devices
  - Pull-to-refresh refreshes data
  - Shortcuts navigate correctly

### TASK-609: PWA Performance Optimization
- [ ] Optimize images with Next.js Image:
  - Replace all `<img>` with `<Image>`
  - Add priority to above-the-fold images
  - Use blur placeholders
  - Specify dimensions
- [ ] Implement code splitting:
  - Lazy load report viewer (`dynamic` import)
  - Lazy load dashboard charts
  - Lazy load model selector (if heavy)
- [ ] Optimize fonts:
  - Use `next/font` for Google Fonts
  - Set `display: 'swap'` to prevent FOIT
  - Preload critical fonts
- [ ] Minimize bundle size:
  - Analyze bundle: `npm run build --analyze`
  - Remove unused dependencies
  - Tree-shake lodash if used
  - Use dynamic imports for large libraries
- [ ] Run Lighthouse audit:
  - Target PWA score >90
  - Performance score >90
  - Accessibility score >90
  - Best Practices score >100

### TASK-610: PWA Testing & Validation
- [ ] Test installation flow:
  - Android Chrome: Install via prompt
  - iOS Safari: Add to Home Screen
  - Desktop Chrome: Install via browser
  - Desktop Edge: Install via browser
- [ ] Test installed app:
  - Opens in standalone mode (no browser chrome)
  - Icons display correctly
  - Splash screen shows (iOS)
  - Theme color applied to status bar
- [ ] Test offline functionality:
  - Install app
  - Go offline
  - Launch app (should work)
  - Navigate pages (should work)
  - View reports (cached ones should work)
  - Try to submit (should queue)
  - Go online (should auto-submit)
- [ ] Test push notifications:
  - Subscribe
  - Submit analysis
  - Lock device
  - Wait for completion
  - Verify notification appears
  - Tap notification → opens app to report
- [ ] Test on low-end devices:
  - Older Android phone (3G network)
  - Verify performance is acceptable
  - Check memory usage
  - Verify no crashes
- [ ] Run PWA validation tools:
  - Lighthouse PWA audit
  - Chrome DevTools → Application → Manifest
  - Chrome DevTools → Application → Service Workers
  - Verify no errors

---

## Phase 7: Ideas Library & Multi-Model Comparison (P0 - Core Features, 12-15 hours)

### TASK-701: Database Setup for Ideas
- [ ] Choose storage approach: PostgreSQL + IndexedDB hybrid
- [ ] Install PostgreSQL in Docker:
  - Add `postgres` service to docker-compose.yml
  - Configure environment variables (DB credentials)
  - Create persistent volume for database
- [ ] Install backend dependencies:
  ```bash
  npm install pg sequelize sequelize-typescript
  npm install --save-dev @types/sequelize
  ```
- [ ] Create database schema:
  - `ideas` table (id, name, description, industry, tags, status, etc.)
  - `idea_versions` table (version history)
  - `idea_attachments` table (file uploads)
- [ ] Add `ideaId` column to `reports` table (link reports to ideas)
- [ ] Create Sequelize models:
  - `Idea` model with relationships
  - `IdeaVersion` model
  - `IdeaAttachment` model
- [ ] Run migrations
- [ ] Test database connection

### TASK-702: Ideas Backend API
- [ ] Create `backend/src/models/Idea.ts`:
  - Define Idea interface
  - Sequelize model with validations
  - Relationships (hasMany reports, hasMany versions)
- [ ] Create `backend/src/routes/ideas.ts`:
  - `POST /api/ideas` - Create new idea
  - `GET /api/ideas` - List all ideas (with pagination, search, filters)
  - `GET /api/ideas/:ideaId` - Get idea details
  - `PUT /api/ideas/:ideaId` - Update idea (creates new version)
  - `DELETE /api/ideas/:ideaId` - Delete idea
  - `POST /api/ideas/:ideaId/versions` - Save new version
  - `GET /api/ideas/:ideaId/reports` - Get all reports for idea
  - `POST /api/ideas/:ideaId/analyze` - Start analysis from saved idea
- [ ] Create `backend/src/services/ideaService.ts`:
  - CRUD operations
  - Search implementation (by name, description, tags)
  - Filter implementation (by status, industry, date range)
  - Sort implementation (recent, name, last analyzed)
  - Version management
- [ ] Add request validation (express-validator)
- [ ] Add error handling
- [ ] Test all endpoints with Postman

### TASK-703: Ideas Library Frontend
- [ ] Create `frontend/app/ideas/page.tsx` (Ideas Library):
  - Header with "New Idea" button
  - Search bar
  - Filter dropdowns (status, industry, tags)
  - Sort dropdown (recent, name, last analyzed, # of analyses)
  - Grid/list view toggle
  - Idea cards showing:
    - Name, description preview (truncated)
    - Industry tag, custom tags
    - Status badge
    - Number of analyses
    - Last analyzed date
    - Quick actions (View, Edit, Analyze, Delete)
  - Pagination or infinite scroll
  - Empty state ("No ideas yet")
- [ ] Create `frontend/components/IdeaCard.tsx`:
  - Card layout with metadata
  - Status badge (draft, ready, analyzing, analyzed, archived)
  - Actions menu
  - Click to view details
- [ ] Create `frontend/components/IdeaFilters.tsx`:
  - Search input with debounce
  - Status filter (multi-select)
  - Industry filter (dropdown)
  - Tags filter (multi-select)
  - Date range picker
  - Clear filters button
- [ ] Implement search functionality (client-side or API)
- [ ] Implement filtering (update URL params)
- [ ] Implement sorting
- [ ] Test on mobile (responsive design)

### TASK-704: New Idea Creation
- [ ] Create `frontend/app/ideas/new/page.tsx` OR modal component:
  - Form fields:
    - Project name* (required, min 3 chars)
    - Industry dropdown (optional, predefined list)
    - Target market radio (B2B, B2C, B2B2C)
    - Estimated budget (number input)
    - Description* (required, min 100 chars, textarea)
    - Tags (multi-select with autocomplete + custom)
    - File upload (alternative to typing, .txt/.md/.docx/.pdf)
    - Notes (optional, textarea)
  - Form validation (Zod or React Hook Form)
  - Character counter for description
  - File upload with drag & drop
  - Parse uploaded file → populate description
- [ ] Create `frontend/components/IdeaForm.tsx`:
  - Reusable form component
  - Validation feedback
  - Auto-save draft (localStorage)
  - Submit button states (Save as Draft, Save and Analyze)
- [ ] Implement form submission:
  - POST to `/api/ideas`
  - Handle success → redirect to idea detail or analyze page
  - Handle errors → show toast
- [ ] Add tag autocomplete:
  - Suggest popular tags
  - Allow custom tags
  - Multi-select UI
- [ ] Test form validation
- [ ] Test file upload

### TASK-705: Idea Detail Page
- [ ] Create `frontend/app/ideas/[ideaId]/page.tsx`:
  - Tab navigation:
    - Overview tab
    - Analyses tab (if any exist)
    - Edit tab
  - Action buttons (Edit, Analyze, Delete, Archive)
- [ ] **Overview Tab**:
  - Display full idea details:
    - Name (h1)
    - Industry, target market, budget (metadata row)
    - Tags (badges)
    - Description (full text, markdown rendered)
    - Notes
    - Created/updated dates
  - Version history section:
    - List all versions
    - Show changes summary
    - Link to view previous version
  - Attachments section (if any)
- [ ] **Analyses Tab**:
  - List all analyses for this idea:
    - Model name
    - Generated date
    - Verdict badge (GO BUILD, PROTOTYPE FIRST, etc.)
    - Overall score
    - Cost
    - Link to view report
  - If 2+ analyses: "Compare Analyses" button
  - If 0 analyses: Empty state with "Analyze Now" CTA
- [ ] **Edit Tab**:
  - Reuse IdeaForm component
  - Pre-populated with current data
  - Save updates → creates new version
  - Version notes field (describe changes)
  - Cancel button
- [ ] Implement delete confirmation:
  - Modal: "Are you sure? This will delete all linked reports."
  - Confirm → DELETE request
  - Redirect to ideas library
- [ ] Test all tabs

### TASK-706: Enhanced Analyze Flow with Ideas
- [ ] Update `frontend/app/analyze/page.tsx`:
  - Add option at top: "Select saved idea OR create new"
  - If "Select saved idea":
    - Dropdown/searchable list of saved ideas
    - Auto-populate description from selected idea
    - Show idea metadata
    - Link analysis to idea on submit
  - If "Create new":
    - Original flow (upload/paste)
    - Optional: "Save to library" checkbox
  - Both flows converge to model selection
- [ ] Update analyze submission:
  - Include `ideaId` in request if using saved idea
  - Backend links report to idea
  - Update idea `lastAnalyzedAt` timestamp
  - Update idea status to "analyzing" → "analyzed"
- [ ] After analysis completes:
  - Redirect to idea detail page (Analyses tab)
  - Show success: "Analysis complete! View report"
- [ ] Test both flows (saved idea vs. new)

### TASK-707: IndexedDB Sync for Offline Ideas (PWA)
- [ ] Install Dexie.js: `npm install dexie`
- [ ] Create `frontend/lib/db.ts`:
  - Define IndexedDB schema for ideas
  - Create Dexie database instance
  - Define tables (ideas, ideaVersions)
- [ ] Implement sync service:
  - On CRUD operation (online):
    - Update PostgreSQL
    - Update IndexedDB cache
  - On CRUD operation (offline):
    - Update IndexedDB only
    - Mark as `pendingSync: true`
    - Queue for background sync
  - On reconnect:
    - Sync pending changes to server
    - Resolve conflicts (server wins)
- [ ] Update Ideas Library to use IndexedDB when offline:
  - Detect offline state
  - Load ideas from IndexedDB
  - Show offline indicator
  - Disable actions requiring server (analyze)
- [ ] Implement background sync for ideas:
  - Register sync event
  - Upload pending changes when online
  - Show sync status in UI
- [ ] Test offline functionality:
  - Create idea offline → sync when online
  - Edit idea offline → sync when online
  - View ideas offline (from cache)

### TASK-708: Ideas Search & Advanced Filters
- [ ] Implement full-text search:
  - Backend: Use PostgreSQL full-text search or ElasticSearch
  - Search across: name, description, notes, tags
  - Rank results by relevance
- [ ] Create `frontend/components/AdvancedFilters.tsx`:
  - Expandable filter panel
  - Multiple filter criteria:
    - Status (draft, analyzed, archived)
    - Industry (multi-select)
    - Tags (multi-select with autocomplete)
    - Date range (created, updated, last analyzed)
    - Has analyses (yes/no)
    - Budget range (min/max)
  - Apply filters button
  - Active filters chips (removable)
  - Clear all filters
- [ ] Implement filter state management:
  - Update URL query params
  - Persist filters in localStorage
  - Load filters on page load
- [ ] Implement saved filter presets:
  - "My drafts" - status:draft
  - "Recently analyzed" - lastAnalyzed:<7 days
  - "Needs validation" - status:analyzed + low scores
- [ ] Add sort options:
  - Most recent
  - Alphabetical (A-Z, Z-A)
  - Last analyzed (recent first)
  - Number of analyses (most to least)
  - Created date (oldest/newest)
- [ ] Test all filter combinations

### TASK-709: Ideas Export/Import
- [ ] Create `GET /api/ideas/export`:
  - Export all ideas as JSON
  - Include: ideas, versions, metadata
  - Exclude: linked reports (just IDs)
  - Return as downloadable file
- [ ] Create `POST /api/ideas/import`:
  - Accept JSON file upload
  - Validate schema
  - Import ideas (create new IDs)
  - Handle duplicates (skip or merge)
  - Return import summary (success/failed count)
- [ ] Add export button to Ideas Library:
  - "Export All Ideas" button
  - Downloads `venturepulse-ideas-2024-01-20.json`
  - Show toast: "X ideas exported"
- [ ] Add import button:
  - File upload input
  - Parse JSON
  - Show preview (# of ideas to import)
  - Confirm import
  - Show progress during import
  - Show results: "Imported 15 ideas, skipped 2 duplicates"
- [ ] Create export/import format:
  ```json
  {
    "exportedAt": "2024-01-20T10:00:00Z",
    "version": "1.0",
    "ideas": [
      {
        "name": "SmartPlate",
        "description": "...",
        "industry": "SaaS",
        "tags": ["AI", "Health"],
        ...
      }
    ]
  }
  ```
- [ ] Test export/import cycle

### TASK-710: Multi-Model Comparison Engine (Backend)
- [ ] Create `backend/src/services/comparisonEngine.ts`:
  - Function `generateComparison(reportIds: string[])`
  - Fetch all reports from database
  - Extract key data from each report:
    - Model name, cost, date
    - Viability scores (5 dimensions + overall)
    - Verdict (GO BUILD, PROTOTYPE, RE-VALIDATE)
    - Top highlight, top risk, next step
  - Calculate comparison statistics:
    - Score spread (max - min)
    - Average scores per dimension
    - Identify high disagreement dimensions (spread >2.0)
  - Identify consensus areas:
    - Where all models agree (spread <1.0)
    - Common recommendations
  - Identify disagreement areas:
    - Where models differ significantly (spread >2.0)
    - Conflicting recommendations
  - Generate recommendation:
    - Which model to trust based on spread
    - Areas needing additional validation
  - Return structured comparison data
- [ ] Create comparison API endpoint:
  - `GET /api/ideas/:ideaId/comparison`
  - `GET /api/compare?reports=id1,id2,id3`
- [ ] Implement caching (optional):
  - Cache comparison in Redis (24h TTL)
  - Invalidate on report change
- [ ] Test comparison engine with mock data

### TASK-711: Multi-Model Comparison Frontend
- [ ] Create `frontend/app/compare/[ideaId]/page.tsx`:
  - Fetch comparison data from API
  - Display comparison header:
    - Idea name
    - Number of models compared
    - Total cost
    - Generated date
  - Comparison sections (see below)
- [ ] Create `frontend/components/comparison/ViabilityScoreComparison.tsx`:
  - Show overall score for each model
  - Progress bars (horizontal)
  - Verdict badges (color-coded)
  - Highlight spread if >1.5 points
  - Visual indicator of disagreement
- [ ] Create `frontend/components/comparison/DimensionBreakdown.tsx`:
  - Table showing 5 dimensions × N models
  - Columns: Dimension, Model 1, Model 2, ..., Average, Spread
  - Color-code spread:
    - Green (<1.0): Consensus
    - Yellow (1.0-2.0): Moderate disagreement
    - Red (>2.0): High disagreement
  - Sort by spread (highest first)
- [ ] Create `frontend/components/comparison/AnalysisInsights.tsx`:
  - Cost vs Quality analysis:
    - List each model with cost and score
    - Highlight best value
  - Consensus areas:
    - Bullet list of areas where models agree
    - Show common scores/recommendations
  - Disagreement areas:
    - Bullet list of high-spread dimensions
    - Explain why models might differ
    - Quote specific differences from reports
  - Recommendation:
    - AI-generated or rule-based
    - "Trust Model X for dimension Y"
    - "Validate assumption Z"
- [ ] Create visualizations:
  - Radar chart (Recharts):
    - 5 dimensions as axes
    - One line per model
    - Overlay to show spread
  - Cost vs Quality scatter plot:
    - X-axis: Cost
    - Y-axis: Overall score
    - Each model as a point
    - Best value highlighted
- [ ] Add export functionality:
  - Export comparison as PDF/HTML
  - Include all charts and insights
  - Downloadable summary
- [ ] Test with 2, 3, and 4 model comparisons

### TASK-712: Detailed Section-by-Section Comparison
- [ ] Create `frontend/components/comparison/SectionComparison.tsx`:
  - Tabbed interface:
    - Overview (default)
    - Executive Summary
    - Market Landscape
    - Technical Feasibility
    - Competitive Advantage
    - Business Model
    - MVP Roadmap
    - Success Metrics
    - Go-to-Market
  - Each tab shows side-by-side comparison:
    - Table: Row = aspect, Columns = models
    - Example for Executive Summary:
      - Verdict
      - Top 3 highlights
      - Top 3 risks
      - Recommended next steps
  - Highlight differences:
    - Color-code conflicting information
    - Show what's unique to each model
- [ ] Extract data from HTML reports:
  - Parse each report HTML
  - Extract structured data (scores, lists, tables)
  - Store in comparison object
- [ ] Implement diff algorithm:
  - Identify similar vs. different content
  - Highlight unique insights per model
- [ ] Add "View Full Report" links:
  - Deep link to specific section in original report
- [ ] Test extraction and comparison

### TASK-713: Auto-Trigger Comparison
- [ ] Update analyze submission flow:
  - When user submits with 2+ models:
    - Create all analysis jobs
    - Wait for all to complete
    - Auto-generate comparison
    - Redirect to comparison page
  - Show progress: "Generating comparison..."
- [ ] Add comparison indicators in UI:
  - Idea detail page: If 2+ reports exist, show "Compare Analyses" button
  - Dashboard: Show comparison icon on ideas with multiple analyses
  - Report page: Show "Compare with other analyses" link
- [ ] Create comparison auto-detection:
  - On report completion, check if idea has multiple reports
  - If yes, create comparison link
  - Notify user: "Comparison available"
- [ ] Test auto-trigger

### TASK-714: AI-Powered Meta-Analysis (Optional Enhancement)
- [ ] Create AI meta-analysis prompt:
  - Input: All report data (scores, verdicts, risks, highlights)
  - Output: Structured analysis of consensus/disagreement
  - Explain why models differ
  - Recommend which analysis to trust
- [ ] Implement backend endpoint:
  - `POST /api/comparison/:comparisonId/meta-analysis`
  - Call OpenRouter with meta-analysis prompt
  - Parse AI response
  - Return structured insights
- [ ] Add to comparison page:
  - "Generate AI Meta-Analysis" button
  - Show loading state
  - Display AI insights:
    - Why models disagree
    - Which model is more reliable
    - Additional validation recommended
- [ ] Cache AI meta-analysis (expensive operation)
- [ ] Test with various comparison scenarios

### TASK-715: Comparison Persistence & Sharing
- [ ] Create `comparisons` table in database:
  - id, ideaId, reportIds[], generatedAt, insights
  - Store generated comparisons for re-access
- [ ] Implement comparison history:
  - User can view past comparisons
  - List all comparisons for an idea
  - Access historical comparisons
- [ ] Create shareable comparison links:
  - Generate unique share token
  - Public URL: `/share/comparison/:token`
  - Expires after 30 days or on delete
- [ ] Add comparison export:
  - Export as PDF (Puppeteer)
  - Export as HTML (self-contained)
  - Export as JSON (raw data)
- [ ] Create share dialog:
  - Copy link button
  - Email share (optional)
  - QR code (optional)
- [ ] Test sharing and persistence

---

## Phase 8: Improvements & Enhancements (Optional, 4-6 hours)

### TASK-501: Add Prompt Improvements
- [ ] Implement "Devil's Advocate" section:
  - Create `prompts/sections/section10-contrarian-analysis.md`
  - Add to analyze-script.sh section array
  - Update create-wrapper.sh navigation
- [ ] Implement "Sensitivity Analysis" section:
  - Create `prompts/sections/section11-sensitivity-analysis.md`
  - Add tables for unit economics variations
- [ ] Update existing prompts based on `ANALYSIS-AND-IMPROVEMENTS.md`:
  - Add team/founder fitness to Executive Summary
  - Add failed competitor analysis to Market Landscape
  - Add dependency risk matrix to Technical Feasibility
- [ ] Test new sections with real analyses

### TASK-502: Add Model Comparison Feature
- [ ] Create `frontend/app/compare/page.tsx`
- [ ] Allow selecting 2-3 reports for same project
- [ ] Display side-by-side comparison:
  - Executive Summary verdicts
  - Viability scores
  - Key differences highlighted
- [ ] Show cost vs. quality tradeoff
- [ ] Recommend which model to use for future analyses

### TASK-503: Add Report Regeneration
- [ ] Add "Regenerate Section" button to report viewer
- [ ] Create `POST /api/reports/:reportId/regenerate/:sectionId`:
  - Create new job for single section
  - Use same project data
  - Use same or different model
  - Replace section in existing report
- [ ] Update report viewer to reload on regeneration
- [ ] Add version history (optional)

### TASK-504: Add User Authentication (Phase 2)
- [ ] Implement NextAuth.js
- [ ] Add sign up / sign in / sign out
- [ ] Add user database (PostgreSQL)
- [ ] Associate reports with users
- [ ] Add user dashboard (separate from public dashboard)
- [ ] Add usage limits per user (10 analyses/month free tier)
- [ ] Add payment integration (Stripe, optional)

### TASK-505: Add Report Sharing
- [ ] Generate unique share URLs for reports
- [ ] Add `GET /share/:shareToken` public route
- [ ] Create share dialog in report viewer:
  - Copy link button
  - QR code (optional)
  - Email share (optional)
- [ ] Add access control (public, private, password-protected)
- [ ] Track share analytics (views, downloads)

### TASK-506: Add Export to PDF
- [ ] Install Puppeteer in worker container
- [ ] Implement PDF export:
  - Render HTML report in headless Chrome
  - Generate PDF
  - Save alongside HTML report
- [ ] Add "Download PDF" button to report viewer
- [ ] Optimize PDF formatting (page breaks, styling)

### TASK-507: Add Webhook Notifications
- [ ] Add webhook URL field to analysis form
- [ ] Send POST request to webhook on completion:
  - Include job status, report URL, metadata
- [ ] Add retry logic for failed webhooks
- [ ] Add webhook logs/history
- [ ] Support Slack/Discord webhook formats

### TASK-508: Add Analytics Dashboard
- [ ] Track metrics:
  - Total analyses run
  - Popular models
  - Average cost per analysis
  - Average generation time
  - Error rate
- [ ] Create admin dashboard to view metrics
- [ ] Add charts (Recharts)
- [ ] Add export to CSV

---

## Phase 7: Deployment & Production (2-3 hours)

### TASK-601: Create Production Docker Compose
- [ ] Create `docker-compose.prod.yml`:
  - Use production builds (NODE_ENV=production)
  - Remove volume mounts for code (use image only)
  - Add health checks for all services
  - Configure restart policies (always)
  - Optimize resource limits (CPU, memory)
- [ ] Create production Dockerfiles with multi-stage builds
- [ ] Minimize image sizes (alpine base, prune dev dependencies)

### TASK-602: Add Nginx Reverse Proxy
- [ ] Create nginx configuration:
  - Route `/api/*` to backend
  - Route `/*` to frontend
  - Add gzip compression
  - Add caching headers
  - Add rate limiting
- [ ] Add to docker-compose as `nginx` service
- [ ] Test with production compose

### TASK-603: Add SSL/HTTPS (Let's Encrypt)
- [ ] Add certbot container to docker-compose
- [ ] Configure nginx for SSL termination
- [ ] Auto-renewal setup
- [ ] Test HTTPS access

### TASK-604: Deployment Documentation
- [ ] Create `docs/DEPLOYMENT.md`:
  - Server requirements (RAM, CPU, disk)
  - Cloud provider guides (AWS, DigitalOcean, GCP)
  - Domain setup
  - SSL configuration
  - Backup strategy
  - Monitoring setup
  - Scaling guide
- [ ] Create deployment scripts:
  - `deploy.sh` for automated deployment
  - `backup.sh` for report backups
- [ ] Document environment variables for production

### TASK-605: Monitoring & Logging
- [ ] Add structured logging (Winston with JSON output)
- [ ] Configure log aggregation (optional: ELK stack, CloudWatch)
- [ ] Add application monitoring (optional: Sentry, DataDog)
- [ ] Add uptime monitoring (optional: UptimeRobot)
- [ ] Create health check dashboard

---

## Testing Checklist

### Unit Tests
- [ ] Backend API endpoints (80%+ coverage)
- [ ] File processing functions
- [ ] Cost estimation logic
- [ ] Queue job processing
- [ ] OpenRouter API client

### Integration Tests
- [ ] Full analysis workflow (upload → process → view)
- [ ] SSE progress streaming
- [ ] Multi-model parallel processing
- [ ] Error handling paths
- [ ] File upload and processing

### E2E Tests (Playwright)
- [ ] User journey: New analysis → View results
- [ ] Model selection and cost calculation
- [ ] Report viewer navigation
- [ ] Dashboard filtering and sorting
- [ ] Delete report flow
- [ ] Error states (invalid file, API error)

### Manual Testing
- [ ] Cross-browser (Chrome, Firefox, Safari, Edge)
- [ ] Mobile responsive (iOS Safari, Chrome Android)
- [ ] Docker on different platforms (Mac, Linux, Windows WSL)
- [ ] Different screen sizes
- [ ] Accessibility (keyboard navigation, screen readers)

---

## Success Criteria

**MVP Launch Ready When**:
- ✅ User can upload project and select models via GUI
- ✅ Reports generate successfully for at least 3 models
- ✅ Progress tracking works in real-time
- ✅ Reports display correctly in viewer
- ✅ Docker containers start with `./run.sh`
- ✅ All tests pass (unit + integration + E2E)
- ✅ Documentation complete (README + User Guide)
- ✅ No critical bugs in core workflow

**Production Ready When**:
- ✅ All MVP criteria met
- ✅ Production Docker setup complete with nginx
- ✅ HTTPS working with valid certificate
- ✅ Monitoring and logging configured
- ✅ Backups automated
- ✅ Performance optimized (sub-3s page loads)
- ✅ Security audit complete
- ✅ Load testing passed (10 concurrent analyses)

---

## Estimated Timeline

**Week 1** (20-25 hours):
- Days 1-2: Phase 1 (Setup) + Phase 2 (Backend)
- Days 3-4: Phase 3 (Frontend)
- Day 5: Phase 4 (Integration & Testing)

**Week 2** (18-24 hours):
- Days 1-2: Phase 5 (Documentation)
- Days 3-4: Phase 6 (PWA Implementation)
- Day 5: Phase 7 (Ideas & Comparison) - Core features

**Week 3** (Optional, 6-10 hours):
- Days 1-2: Phase 7 (Ideas & Comparison) - Advanced features
- Day 3: Phase 8 (Enhancements, optional) + Phase 9 (Deployment)
- Days 4-5: Final testing and polish

**Total**:
- **MVP with PWA**: 35-45 hours
- **MVP with PWA + Ideas + Basic Comparison**: 47-60 hours
- **Full implementation with all features**: 55-70 hours

---

## Priority Levels

**P0 (Must Have for MVP)**:
- Tasks 001-005, 101-110, 201-210, 301-305, 401-405

**P1 (Highly Recommended - Core Value Features)**:
- Tasks 601-610 (PWA implementation for mobile-first experience)
- Tasks 701-709 (Ideas Library - save, manage, and reuse project ideas)
- Tasks 710-713 (Multi-Model Comparison - when analyzing with 2+ models)

**P2 (Nice to Have - Enhanced Features)**:
- Tasks 714-715 (AI meta-analysis, comparison sharing)
- Tasks 501-503 (Prompt improvements, report regeneration)

**P3 (Post-MVP)**:
- Tasks 504-508 (Authentication, sharing, PDF export, webhooks, analytics)
- Tasks 801-805 (Production deployment)

---

This task list provides a complete roadmap for transforming VenturePulse into a production-ready web application. Each task is actionable and can be completed independently (with some dependencies noted).
