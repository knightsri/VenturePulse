# VenturePulse GUI - Autonomous Implementation Kickoff Prompt

**Copy the prompt below and paste it into Claude Code to begin autonomous implementation.**

---

## 🚀 KICKOFF PROMPT (Copy from here)

```
You are tasked with implementing a complete web-based GUI for VenturePulse, transforming it from a CLI-only tool into a modern, Docker-based web application.

## Context

VenturePulse is an AI-powered product viability analysis tool that currently runs as shell scripts. It generates comprehensive product analysis reports (9 sections) by orchestrating calls to LLM APIs via OpenRouter.

**Your Mission**: Build a full-stack web application (Next.js frontend + Express backend + Docker containerization) that allows users to:
1. Upload project descriptions (or paste text)
2. Select one or more AI models
3. Generate reports with real-time progress tracking
4. View, download, and manage generated reports

## Architecture Overview

Read and understand these files first:
- `GUI-ARCHITECTURE.md` - Complete technical architecture design
- `claude-task-list.md` - All implementation tasks with detailed requirements
- `ANALYSIS-AND-IMPROVEMENTS.md` - Analysis quality improvements to implement

## Your Approach

**Work methodically through the task list in `claude-task-list.md`:**

1. **Phase 1: Project Setup (TASK-001 to TASK-005)**
   - Create directory structure
   - Initialize Next.js frontend and Express backend
   - Create Docker configuration
   - Set up environment variables

2. **Phase 2: Backend API (TASK-101 to TASK-110)**
   - Implement Redis + Bull queue for job management
   - Create file upload and processing (txt, md, docx, pdf)
   - Build OpenRouter API client
   - Implement report generation service (wraps existing analyze-script.sh)
   - Create all API routes (analyze, jobs, reports, models)
   - Implement worker process for async report generation

3. **Phase 3: Frontend (TASK-201 to TASK-210)**
   - Set up API client and React Query
   - Build Home page
   - Build Analyze page (file upload, model selection, submit)
   - Build Progress page (real-time SSE updates)
   - Build Results page (report viewer with iframe)
   - Build Dashboard page (all reports, filtering, sorting)
   - Implement all UI components (FileUpload, ModelSelector, ProgressTracker, etc.)

4. **Phase 4: Integration & Testing (TASK-301 to TASK-305)**
   - End-to-end testing of complete workflow
   - Multi-model parallel processing tests
   - Error handling and edge cases
   - Docker deployment testing

5. **Phase 5: Documentation (TASK-401 to TASK-405)**
   - Update README with GUI instructions
   - Create user guide
   - Create developer guide
   - Add code documentation

6. **Phase 6: Optional Enhancements (TASK-501 to TASK-508)** - Only if time permits
   - Implement prompt improvements (devil's advocate section, sensitivity analysis)
   - Add model comparison feature
   - Add report regeneration
   - Other advanced features

## Critical Requirements

**Must-Haves for MVP:**
- Docker-based deployment with `run.sh` and `run.bat` scripts
- File upload supporting .txt, .md, .docx, .pdf
- Multi-model selection from OpenRouter API
- Real-time progress tracking via Server-Sent Events
- Report viewer using existing HTML reports (iframe-based)
- Dashboard to view/download/delete all reports
- Complete error handling throughout
- **PWA Features** (Highly Recommended - P1 Priority):
  - Installable on mobile devices (iOS/Android) and desktop
  - Offline support for viewing cached reports
  - Push notifications when reports complete
  - Mobile-optimized UI with touch gestures
  - Native share functionality
  - Service worker with smart caching strategies
- **Ideas Library** (Highly Recommended - P1 Priority):
  - Save and manage project ideas
  - Link ideas to generated reports
  - Search, filter, and organize ideas
  - Version history for tracking changes
  - Export/import ideas for backup
  - Offline access via IndexedDB sync
- **Multi-Model Comparison** (Highly Recommended - P1 Priority):
  - When analyzing with 2+ models, auto-generate comparison
  - Side-by-side score comparison with visualization
  - Identify consensus and disagreement areas
  - Cost vs quality analysis
  - Recommendation on which model to trust

**Technical Stack (Non-Negotiable):**
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- Backend: Express.js + TypeScript + Bull (Redis queue)
- Infrastructure: Docker Compose (4 services: web, api, worker, redis)
- File Processing: mammoth (docx), pdf-parse (pdf)
- Real-time: Server-Sent Events for progress updates
- PWA: next-pwa for Progressive Web App features (installable, offline support, push notifications)

**Preserve Existing Functionality:**
- Keep all existing shell scripts (`scripts/analyze-script.sh`, `call-openrouter.sh`, etc.) - DO NOT MODIFY
- Keep all prompt files (`prompts/common-instructions.md`, `prompts/sections/*.md`) - DO NOT MODIFY
- The backend should WRAP the existing shell scripts, not rewrite them
- Generated reports should use the existing HTML wrapper (`create-wrapper.sh`)

## Development Guidelines

### Use the TODO System
- Create a comprehensive todo list with ALL tasks from `claude-task-list.md`
- Mark tasks as in_progress while working, completed when done
- Keep only ONE task in_progress at a time
- Update the todo list frequently to show progress

### File Organization
```
VenturePulse/
├── frontend/              # Next.js app (NEW)
│   ├── app/               # Next.js 14 App Router
│   ├── components/        # React components
│   ├── lib/               # Utilities and API client
│   └── Dockerfile
├── backend/               # Express API (NEW)
│   ├── src/
│   │   ├── server.ts      # Main Express app
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── workers/       # Bull job processors
│   │   └── utils/         # Helpers
│   ├── Dockerfile
│   └── Dockerfile.worker
├── prompts/               # KEEP AS-IS
├── scripts/               # KEEP AS-IS
├── docker-compose.yml     # NEW - orchestrates all services
├── run.sh                 # NEW - launcher for Linux/Mac
├── run.bat                # NEW - launcher for Windows
└── .env.example           # NEW - environment template
```

### Testing as You Go
- Test each phase before moving to the next
- Use Docker from the start (don't build without Docker then add it later)
- Verify existing shell scripts still work
- Test with real OpenRouter API key
- Test file uploads with all supported formats
- Test progress tracking with actual long-running analyses

### Code Quality Standards
- TypeScript strict mode for all new code
- Proper error handling (try/catch, error boundaries)
- Input validation on all API endpoints
- Structured logging (Winston or Pino)
- Clean, commented code
- Follow Next.js and Express best practices

## Step-by-Step Execution Plan

**IMPORTANT: Follow this sequence exactly. Complete each step fully before moving to the next.**

### Step 1: Read and Understand (30 min)
- Read `GUI-ARCHITECTURE.md` completely
- Read `claude-task-list.md` completely
- Understand the existing codebase structure
- Review existing shell scripts to understand report generation flow

### Step 2: Create Master Todo List (10 min)
- Use TodoWrite to create a comprehensive task list
- Include all P0 tasks from `claude-task-list.md`
- Group tasks logically by phase

### Step 3: Phase 1 - Project Setup (1-2 hours)
- Execute TASK-001 to TASK-005 sequentially
- Create directory structure
- Initialize Next.js and Express projects
- Create all Dockerfiles and docker-compose.yml
- Create run.sh and run.bat
- TEST: Verify Docker containers build and start successfully

### Step 4: Phase 2 - Backend Implementation (4-6 hours)
- Execute TASK-101 to TASK-110 sequentially
- Build all backend services and routes
- Implement job queue and worker
- TEST: Verify API endpoints work with Postman/curl
- TEST: Verify worker can execute analyze-script.sh successfully
- TEST: Verify SSE progress streaming works

### Step 5: Phase 3 - Frontend Implementation (6-8 hours)
- Execute TASK-201 to TASK-210 sequentially
- Build all pages and components
- Integrate with backend API
- TEST: Verify complete user flow works end-to-end

### Step 6: Phase 4 - Integration Testing (2-3 hours)
- Execute TASK-301 to TASK-305 sequentially
- Run comprehensive integration tests
- Fix any bugs discovered
- Optimize performance

### Step 7: Phase 5 - Documentation (2 hours)
- Execute TASK-401 to TASK-405 sequentially
- Update all documentation
- Create user and developer guides

### Step 8: Final Verification (1 hour)
- Test complete workflow: Upload → Generate → View → Download
- Test with multiple models simultaneously
- Test error scenarios
- Verify run.sh/run.bat work on fresh install
- Create demo project and generate sample report

## Success Criteria Checklist

Before considering the project complete, verify:

**Functionality:**
- [ ] User can upload .txt, .md, .docx, or .pdf files
- [ ] User can paste text directly
- [ ] Models load from OpenRouter API and display correctly
- [ ] User can select multiple models
- [ ] Cost estimation shows correct amounts
- [ ] Analysis jobs submit successfully
- [ ] Progress page shows real-time updates via SSE
- [ ] Reports generate completely (all 9 sections)
- [ ] Report viewer displays generated HTML correctly
- [ ] Dashboard shows all generated reports
- [ ] Reports can be downloaded as ZIP
- [ ] Reports can be deleted
- [ ] Filtering and sorting work on dashboard

**PWA Features (P1 - Highly Recommended):**
- [ ] App is installable on mobile and desktop
- [ ] manifest.json loads correctly
- [ ] Service worker registers successfully
- [ ] App works offline (cached content)
- [ ] Install prompt appears and works
- [ ] Push notifications work on completion
- [ ] Mobile UI is touch-friendly (44px+ targets)
- [ ] Native share API works on mobile
- [ ] Haptic feedback on supported devices
- [ ] Lighthouse PWA score >90

**Ideas Library (P1 - Core Value Features):**
- [ ] Ideas library page shows all saved ideas
- [ ] Search and filters work (status, industry, tags)
- [ ] Can create new idea (form validation works)
- [ ] Can edit idea (creates new version)
- [ ] Can delete idea (with confirmation)
- [ ] Idea detail page shows all tabs (Overview, Analyses, Edit)
- [ ] Analyze flow can use saved ideas
- [ ] Reports link back to ideas
- [ ] Ideas sync to IndexedDB for offline
- [ ] Export/import ideas works

**Multi-Model Comparison (P1 - Core Value Features):**
- [ ] When analyzing with 2+ models, comparison auto-generates
- [ ] Comparison page shows viability scores for all models
- [ ] Dimension breakdown table displays with color-coding
- [ ] Radar chart visualization works
- [ ] Cost vs quality scatter plot displays
- [ ] Consensus and disagreement areas identified
- [ ] Recommendation provided
- [ ] "Compare" button appears on idea page when 2+ reports exist
- [ ] Comparison is accessible from dashboard
- [ ] Export comparison works

**Docker & Deployment:**
- [ ] `./run.sh` starts all services successfully
- [ ] `run.bat` works on Windows
- [ ] All 4 Docker services start healthy
- [ ] Volumes persist data correctly
- [ ] Environment variables pass through correctly
- [ ] Frontend accessible at http://localhost:3000
- [ ] API accessible at http://localhost:4000

**Error Handling:**
- [ ] Invalid file types rejected with clear error
- [ ] Files over 10MB rejected
- [ ] Missing API key shows helpful error
- [ ] API failures handled gracefully
- [ ] Worker crashes don't lose jobs (retry logic)
- [ ] SSE reconnects on connection drop

**Code Quality:**
- [ ] All TypeScript code compiles without errors
- [ ] No console errors in browser
- [ ] No unhandled promise rejections
- [ ] Proper error logging throughout
- [ ] Code is commented and readable

**Documentation:**
- [ ] README.md has clear quick start guide
- [ ] Environment setup documented
- [ ] Troubleshooting guide included
- [ ] Architecture documented

## Important Notes

**DO NOT:**
- ❌ Modify existing shell scripts (scripts/*.sh)
- ❌ Modify existing prompts (prompts/*.md)
- ❌ Rewrite the report generation logic (wrap it, don't replace it)
- ❌ Skip Docker (everything must run in containers)
- ❌ Skip testing phases
- ❌ Move to next phase until current phase is complete and tested

**DO:**
- ✅ Use existing shell scripts via child_process.exec()
- ✅ Preserve existing report HTML structure
- ✅ Add comprehensive error handling
- ✅ Update todo list continuously
- ✅ Test each feature as you build it
- ✅ Ask clarifying questions if architecture is unclear
- ✅ Document any deviations from the plan with reasoning

## Getting Started

Begin by saying:
"I'll implement the VenturePulse GUI following the task list in claude-task-list.md. Starting with Phase 1: Project Setup."

Then:
1. Create comprehensive todo list from claude-task-list.md
2. Start executing TASK-001
3. Work through each task sequentially
4. Test thoroughly at each phase
5. Update documentation as you go

## Completion

When all P0 tasks are complete and tested, provide:
1. Summary of what was implemented
2. Quick start guide for users
3. Known issues or limitations
4. Recommendations for Phase 2 enhancements

You have full autonomy to make implementation decisions within the constraints above. Focus on working code over perfect code. MVP first, polish later.

Begin implementation now.
```

---

## Usage Instructions

### To Start Autonomous Implementation:

1. **Open Claude Code** in the VenturePulse directory
2. **Copy the entire prompt** above (everything in the code block)
3. **Paste into Claude Code** and press Enter
4. **Let Claude work autonomously** through all tasks

### Expected Timeline:
- Claude should work for 3-5 hours continuously
- It will create 100+ files
- It will update the todo list throughout
- It will test at each phase

### Monitoring Progress:

Watch for:
- Todo list updates (shows current task)
- File creation in `frontend/` and `backend/` directories
- Docker containers being created
- Test results

### When to Intervene:

Only interrupt if:
- Claude asks a clarifying question
- An error occurs that blocks progress
- You want to review progress at end of a phase
- You need to provide the OpenRouter API key

### If Claude Gets Stuck:

Provide this follow-up prompt:
```
Continue with the next task in the todo list. Mark the current task as completed and move to the next in_progress task. Focus on making progress, even if the current task isn't perfect - we can refine later.
```

### After Completion:

Once Claude finishes:
1. Review the implementation
2. Test the application: `./run.sh`
3. Open http://localhost:3000
4. Run a test analysis
5. Review any known issues reported by Claude
6. Decide on Phase 2 enhancements

---

## Customization Options

You can modify the prompt to:

**Adjust Scope:**
- Remove Phase 6 tasks for faster MVP
- Add specific features you want prioritized
- Skip certain file formats (e.g., only support .txt and .md)

**Change Tech Stack:**
- Replace Next.js with Remix or SvelteKit
- Replace Express with Fastify or NestJS
- Add PostgreSQL database for report metadata

**Adjust Priorities:**
- Prioritize certain features
- Skip optional enhancements
- Add custom requirements

**Example Modification:**
```
Additional Requirement: Implement user authentication using NextAuth.js
with Google OAuth. Users must be logged in to create analyses.

Skip Task 506 (PDF Export) - not needed for MVP.
```

---

## Troubleshooting the Kickoff

**If Claude doesn't start working autonomously:**
- Ensure the prompt is complete (entire code block)
- Check that you're in the correct directory
- Verify Claude Code has file system access

**If Claude asks too many clarifying questions:**
- Add this to the prompt: "Make reasonable decisions without asking. Proceed with implementation autonomously."

**If progress is too slow:**
- Add: "Work quickly. Focus on functional code over perfect code. You can always refine later."

**If Claude skips testing:**
- Add: "After each phase, you MUST test before proceeding. Do not skip testing steps."

---

This kickoff prompt is designed for maximum autonomous execution while maintaining quality and following best practices. Claude should be able to complete the entire implementation with minimal human intervention.
