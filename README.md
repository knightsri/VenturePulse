
# 🎯 VenturePulse

> **AI-powered product viability analysis in about an hour, not weeks**

Turn weeks of market research, competitive analysis, and strategic planning into a comprehensive AI-generated report suite. Quick validation in ~25 minutes, full VC-ready analysis in ~60-90 minutes.

---

## 🚀 What is VenturePulse?

VenturePulse is a **prompt library + CLI/Web orchestrator** that generates McKinsey-quality product viability reports using AI. It analyzes your product idea across **19 critical dimensions** (plus Provenance), organized into four strategic phases:

### 🔍 Foundation (Understanding the Problem)
1. **Executive Summary** - Viability scores, verdict, key highlights, recommended next steps
2. **Market Landscape** - Competitors, timing, TAM/SAM/SOM, white space analysis
3. **User Stories** - Core personas, jobs-to-be-done, problem scenarios
4. **Comparable Companies** - Direct/indirect competitors, case studies, market positioning
5. **User Research** - Research methodology, validation approach, interview guides
6. **Validation Experiments** - Hypothesis testing, experiment design, success criteria

### 🏗️ Strategy (Building the Solution)
7. **Technical Feasibility** - Architecture, complexity, AI/low-code implementation, risks
8. **Competitive Advantage** - Moats, defensibility, competitive scoring matrix
9. **Business Model** - Pricing, unit economics, financial projections
10. **Legal & Compliance** - Regulatory requirements, IP considerations, privacy

### 🚀 Execution (Launching & Growing)
11. **MVP Roadmap** - Feature prioritization matrix, phased timeline, implementation strategy
12. **Customer Journey** - Acquisition to advocacy lifecycle, touchpoints
13. **Go-to-Market** - ICP analysis, distribution channels, acquisition strategy
14. **Partnerships** - Strategic alliances, integration opportunities, ecosystem
15. **Expansion Plan** - Geographic/vertical growth strategy, market entry

### 📈 Future (Scaling & Exits)
16. **Success Metrics** - KPIs across technical/engagement/business dimensions, risk register
17. **Funding Strategy** - Capital requirements, investor narrative, fundraising roadmap
18. **Exit Strategy** - Acquisition targets, exit timeline, valuation drivers
19. **Pitch Narrative** - Compelling story, key messages, presentation framework
20. **Provenance** - Analysis transparency, model details, generation timestamp

**The output:** Up to 20 beautifully formatted HTML reports—each independently comprehensive and presentation-ready. Choose **Quick Analysis** (7 core sections) or **Full Analysis** (all 19 sections).

---

## ✨ Why VenturePulse?

### The Old Way (2-3 weeks)
- ❌ 30+ fragmented AI conversations
- ❌ Manual research across competitors, pricing, tech stack
- ❌ Scattered insights in notes, docs, spreadsheets
- ❌ Missing critical dimensions (compliance, risks, defensibility)
- ❌ No structured decision framework

### The VenturePulse Way (25-90 minutes)
- ✅ One command generates up to 19 comprehensive reports
- ✅ Quick Analysis (7 sections) or Full Analysis (19 sections)
- ✅ Automated competitive research and market analysis
- ✅ Structured scoring across all viability dimensions
- ✅ Professional formatting ready for stakeholders/investors
- ✅ Costs $0 (free models) to $10 (premium full analysis)

**What used to cost thousands in consulting fees now costs the price of a coffee.**

---

## ⚡ Quick Start

### Prerequisites

- [OpenRouter API key](https://openrouter.ai/keys) (free tier available)
- **For Web UI (Recommended):** Python 3.11+ or Docker
- **For CLI:** Bash (Mac/Linux/WSL/Git Bash), `curl`, `jq`

### Installation

```bash
# Clone the repository
git clone https://github.com/knightsri/VenturePulse.git
cd VenturePulse
```

### Option 1: Web UI (Recommended)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the Streamlit app (default port 8501)
streamlit run app/venturepulse.py

# Open http://localhost:8501 in your browser
# Enter your OpenRouter API key in the sidebar
```

**Or with Docker:**
```bash
# Create .env with your API key (see .env.example)
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

docker-compose up
# Open http://localhost:8501 (or custom PORT from .env)
```

### Option 2: CLI

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Set your API key
export OPENROUTER_API_KEY="your_key_here"

# Run analysis
./scripts/analyze-script.sh examples/sample-project/smartplate-idea.md

# View the reports
open examples/sample-project/smartplate-idea-analysis-*/index.html
```

**Time estimates:**
- Quick Analysis (7 sections): ~25 minutes
- Full Analysis (19 sections): ~60-90 minutes

---

## 🌐 Web UI Features

The Streamlit-based web interface is the recommended way to use VenturePulse.

### Features

- 📤 **Upload specs** - Drag & drop or paste your project specification
- 🤖 **Multi-model analysis** - Run the same spec through multiple AI models
- ⚡ **Sequential or Parallel** - Choose execution mode for multi-model runs
- 🔀 **Parallel section generation** - Generate all sections simultaneously for faster analysis
- 📊 **Real-time progress** - See elapsed time, cost, and retry status
- 🔄 **Automatic retries** - Failed sections retry with exponential backoff
- 💰 **Cost tracking** - See per-section and total costs in Provenance
- 🔬 **Compare results** - Side-by-side comparison of outputs from different models
- 📚 **Analysis history** - Browse and view past analyses
- 🔑 **API key management** - Enter via UI or environment variable

### Quick Start (Docker)

```bash
# Clone and configure
git clone https://github.com/knightsri/VenturePulse.git
cd VenturePulse
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run with Docker Compose
docker-compose up

# Open http://localhost:8501 (or custom PORT from .env)
```

### Quick Start (Local Python)

```bash
# Clone and setup
git clone https://github.com/knightsri/VenturePulse.git
cd VenturePulse

# Install dependencies
pip install -r requirements.txt

# Configure (optional - can enter API key in UI)
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run Streamlit
streamlit run app/venturepulse.py

# Open http://localhost:8501 (or custom PORT from .env)
```

### Multi-Model Comparison

The web UI lets you:
1. **Select multiple models** from the sidebar dropdown
2. **Choose execution mode** - Sequential (safer) or Parallel (faster)
3. **Compare results** in the "Compare Results" tab with:
   - Side-by-side section comparison
   - Timing metrics per model
   - Section-by-section browsing

---

## 📖 Usage

### Basic Usage

```bash
./scripts/analyze.sh <project-file.md>
```

Uses the default free model (`google/gemini-2.0-flash-exp:free`)

### Choose a Different Model

```bash
# Best free option (recommended for testing)
./scripts/analyze.sh my-idea.md google/gemini-2.0-flash-exp:free

# Premium quality (recommended for serious validation)
./scripts/analyze.sh my-idea.md anthropic/claude-sonnet-4.5

# Balanced quality/cost
./scripts/analyze.sh my-idea.md google/gemini-2.5-pro

# Budget option
./scripts/analyze.sh my-idea.md deepseek/deepseek-chat
```

### See All Options

```bash
./analyze.sh --help
```

---

## 🤖 Recommended Models

VenturePulse works with 100+ models via [OpenRouter](https://openrouter.ai/models). These are the tested, reliable models available in the UI:

### ⭐ Best for VenturePulse

| Model | Speed | Quality | Cost (Full 19) | Best For |
|-------|-------|---------|----------------|----------|
| `anthropic/claude-sonnet-4` | ⚡ Slower | ✅✅✅ **Best** | 💰💰💰 ~$5-10 | Investor-ready analysis |
| `anthropic/claude-3.5-sonnet` | ⚡ Slower | ✅✅✅ Excellent | 💰💰💰 ~$4-8 | Detailed strategic analysis |
| `openai/gpt-4o` | ⚡⚡ Medium | ✅✅ Very Good | 💰💰 ~$3-6 | Balanced speed & quality |
| `openai/gpt-4o-mini` | ⚡⚡⚡ Fast | ✅ Good | 💰 ~$0.30-0.60 | Quick validation |
| `google/gemini-2.5-pro` | ⚡⚡ Medium | ✅✅ Excellent | 💰💰 ~$3-5 | Solid validation |
| `deepseek/deepseek-chat` | ⚡⚡⚡ Fast | ✅ Good | 💰 ~$0.30-0.50 | Budget-friendly testing |
| `deepseek/deepseek-v3.2` | ⚡⚡ Medium | ✅✅ Very Good | 💰 ~$0.50-1.00 | GPT-5 class reasoning |
| `x-ai/grok-4.1-fast` | ⚡⚡⚡ Fast | ✅✅ Good | 💰 FREE | 2M context, agentic |
| `x-ai/grok-4-fast` | ⚡⚡⚡ Fast | ✅✅ Good | 💰💰 ~$1-3 | 2M context, multimodal |
| `qwen/qwen3-max` | ⚡⚡ Medium | ✅✅ Good | 💰 ~$0.50-1.00 | 256K context, multilingual |
| `qwen/qwen-2.5-72b-instruct` | ⚡⚡ Medium | ✅ Good | 💰 ~$0.30-0.60 | Structured output |
| `z-ai/glm-4.7` | ⚡⚡ Medium | ✅✅ Good | 💰 ~$0.50-1.00 | 203K context, coding |
| `z-ai/glm-4.5-air` | ⚡⚡⚡ Fast | ✅ Good | 💰 ~$0.20-0.40 | Budget-friendly |
| `mistralai/mistral-large` | ⚡⚡ Medium | ✅✅ Good | 💰💰 ~$2-4 | European alternative |
| `meta-llama/llama-3.3-70b-instruct` | ⚡⚡ Medium | ✅ Good | 💰 ~$0.50-1.00 | Open source option |

**My recommendation:** Start with **GPT-4o-mini**, **DeepSeek**, or **Grok-4.1-fast** (free!) for quick validation. For investor-ready analysis, use **Claude Sonnet 4** or **Gemini 2.5 Pro**—the depth is worth every penny.

**See all models:** https://openrouter.ai/models

---

## 📁 Project Structure

```
VenturePulse/
├── app/
│   └── venturepulse.py                 # Streamlit web UI (recommended)
├── prompts/
│   ├── common-instructions.md          # Shared analysis guidelines
│   └── sections/
│       ├── section01-executive-summary.md
│       ├── section02-market-landscape.md
│       └── ... (19 total section prompts)
├── scripts/
│   ├── analyze-script.sh              # Main CLI orchestrator
│   ├── call-openrouter.sh             # OpenRouter API wrapper
│   ├── create-wrapper.sh              # HTML wrapper generation
│   ├── generate-provenance.sh         # Metadata generation
│   └── createindex.py                 # Index page generator
├── templates/
│   └── wrapper.html                   # HTML template for reports
├── examples/
│   └── sample-project/
│       └── smartplate-idea.md         # Sample project description
├── Dockerfile                          # Docker build config
├── docker-compose.yml                  # Docker Compose config
├── requirements.txt                    # Python dependencies
├── CLAUDE.md                           # Claude Code guidance
└── README.md
```

---

## 💡 How It Works

### The Architecture

**Current approach (v2.0):** Sequential specialized prompts → 19 focused HTML reports + Provenance
- ✅ Each section uses tailored prompts for that analysis type
- ✅ Web UI with multi-model comparison and cost tracking
- ✅ Quick (7 sections) or Full (19 sections) analysis modes
- ✅ Easy to regenerate any individual section
- ✅ Better handling of complex projects

### The Process

1. **You provide:** A markdown/text file describing your product idea (1-3 pages ideal)

2. **VenturePulse orchestrates:**
   - Loads common analysis instructions
   - Sequentially generates up to 19 specialized reports:
     - Each section calls OpenRouter API with your chosen model
     - Later sections reference insights from earlier reports
     - Each generates its own styled HTML file
   - Creates provenance metadata for transparency

3. **You get:** all comprehensive HTML reports in a timestamped folder

**Total time:** 25-90 minutes depending on analysis depth (varies by model)
**Total cost:** $0 (free models) to $5-15 (premium full analysis)

---

## 🎨 What You Get

### Report Structure

Each analysis creates **separate HTML files** in a timestamped folder:

```
my-idea-analysis-model-20241021-143052/
├── index.html                          ⭐ Start here (CLI only)
├── section01-executive-summary.html
├── section02-market-landscape.html
├── section03-user-stories.html
├── ... (up to 19 sections)
├── section19-pitch-narrative.html
├── section20-provenance.html
├── project-spec.md                     (Web UI)
└── metadata.json                       (Web UI)
```

### Key Features

- **Professional Design:** Executive-ready styling, modern UI
- **Standalone Reports:** Each HTML works independently—easy to share specific sections
- **Rich Visualizations:** Scoring matrices, competitive comparisons, feature prioritization grids
- **Comprehensive Coverage:** 4,000-8,000 total words across all dimensions
- **Portable:** No external dependencies, works offline, easy to email/share
- **Print-Ready:** Professional formatting for hard copies

### What Makes the Reports Valuable

**Executive Summary** gives you:
- Clear GO BUILD / PROTOTYPE FIRST / RE-VALIDATE verdict
- Top 3 highlights of your idea
- Viability scores across 5 dimensions (1-10 scale)
- Critical success factors and key risks
- Recommended next steps

**Market Landscape** includes:
- 3-5 existing competitors with detailed analysis
- Competitive scoring matrix (your idea vs. alternatives)
- Market timing rationale ("Why now?")
- White space identification
- TAM/SAM/SOM estimates

**Success Metrics** provides:
- Specific KPIs across technical, engagement, and business dimensions
- Example: *"99.5% system uptime, 45% 30-day retention, 4.7x LTV:CAC ratio"*
- Risk register with probability, impact, and mitigations
- Comprehensive scoring with gap analysis

**...and 16 more equally detailed reports covering user stories, legal compliance, customer journey, partnerships, funding strategy, and more.**

---

## 📝 Creating Your Project File

Your project description can be simple or comprehensive. Here's what works best:

### Minimum Required (works fine)
- Project name and one-sentence description
- Problem you're solving
- Target audience
- Proposed solution

### Recommended for Best Results
- Business model ideas or pricing thoughts
- Technical approach (if you have preferences)
- Market opportunity (if known)
- Key competitors you're aware of
- Your background/resources/constraints
- Any specific concerns or risks

**Example:** See `examples/sample-project/smartplate-idea.md`

**Format:** Markdown (.md), plain text (.txt), or PDF

**Length:** 1-3 pages is ideal, but more is fine—the tool handles it

---

## 🎯 Real-World Use Cases

Since releasing VenturePulse, it's been used for:

### Side Project Validation
*"Should I spend my weekends building this?"*
- Get clear go/no-go decision in under 2 hours vs. 2-3 weeks of research

### Startup Pivot Decisions
*"We're considering building an application of -so-and-so- domain — does it work?"*
- Run comparative analyses of competition and feasibility

### Client Proposals
*"A client wants us to build X—is it viable?"*
- Generate feasibility report before committing resources

### Investment Due Diligence
*"We're looking at investing in a potential startup—what are the real risks?"*
- Independent AI-powered analysis of the opportunity

### Academic/Learning
*"I want to understand product strategy better"*
- Study the framework and analysis approach

---

## 🛠️ Advanced Usage

### Debug Mode

```bash
export VENTUREPULSE_DEBUG=1
./scripts/analyze.sh my-idea.md
```

Shows token usage, API response details, and generation progress.

### Custom Output Directory

```bash
./scripts/analyze.sh my-idea.md
# Automatically creates: my-idea-analysis-20241021-143052/
```

Timestamped folders preserve multiple analysis runs across the same-model.

### Regenerate Single Section

```bash
# Regenerate just the Market Landscape report
cd my-idea-analysis-model-20241021-143052/
../../scripts/call-openrouter.sh "anthropic/claude-sonnet-4.5" \
  "$(cat ../prompts/sections/section02-market-landscape.md)" \
  "$(cat ../my-idea.md)" \
  > market-landscape.html
```

### Compare Different Models

```bash
# Run same idea through free and premium models
./scripts/analyze.sh my-idea.md google/gemini-2.0-flash-exp:free
./scripts/analyze.sh my-idea.md anthropic/claude-sonnet-4.5

# Compare the executive summaries
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `PORT` | `8501` | Application port (Streamlit) |
| `DEFAULT_MODEL` | `anthropic/claude-sonnet-4` | Pre-selected model in UI |
| `MAXRETRY` | `3` | Maximum retry attempts for failed API calls |
| `MAX_PARALLEL_SECTIONS` | `10` | Maximum concurrent section generation workers |

Example `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
PORT=8888                            # Run on custom port
DEFAULT_MODEL=openai/gpt-4o          # Change default model
MAXRETRY=5                           # Retry up to 5 times
MAX_PARALLEL_SECTIONS=5              # Use up to 5 parallel workers
```

### Retry Logic

VenturePulse automatically retries failed API calls with exponential backoff + jitter:
- **Retryable errors:** Rate limits, timeouts, server errors (502/503/504)
- **Non-retryable errors:** Invalid API key, model not found, content policy violations
- **Backoff formula:** `base_delay * (2 ^ attempt) + random(0, jitter_max)`
  - Example: attempt 1 = ~2-4s, attempt 2 = ~4-6s, attempt 3 = ~8-10s

Failed sections after max retries are marked in the Provenance report with error details.

### Parallel Section Generation

Enable the "Parallel Section Generation" toggle in the UI to generate all sections simultaneously:
- **Faster:** Completes Full Analysis in ~15-25 minutes vs. ~60-90 minutes sequential
- **Trade-off:** Uses more API quota simultaneously (may hit rate limits on free tiers)
- **Best for:** Premium models with higher rate limits

### Set Default Model

**Web UI:** Set `DEFAULT_MODEL` in your `.env` file:
```bash
DEFAULT_MODEL=openai/gpt-4o
```

**CLI:** Edit `scripts/analyze-script.sh`:
```bash
# Change this line:
DEFAULT_MODEL="google/gemini-2.0-flash-exp:free"
# To your preferred model
```

### Adjust API Parameters

Edit `scripts/call-openrouter.sh`:
- `max_tokens`: 25192 (increase for longer outputs)
- `temperature`: 0.7 creative, 0.2 precision (varies by section)
- `top_p`: 0.95 (nucleus sampling)

### Customize Analysis Sections

Edit prompt files in `prompts/sections/`:
- Modify existing section prompts
- Add domain-specific questions
- Adjust scoring criteria
- Change output format

**This is encouraged!** Fork and customize for your industry/domain.

---

## 🐛 Troubleshooting

### "OPENROUTER_API_KEY not set"
```bash
export OPENROUTER_API_KEY="your_key_here"

# For persistence, add to ~/.bashrc or ~/.zshrc:
echo 'export OPENROUTER_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### "jq command not found"
```bash
# Mac
brew install jq

# Linux (Ubuntu/Debian)
sudo apt-get install jq

# Linux (Fedora/RHEL)
sudo dnf install jq

# Windows (Git Bash)
# Download from https://jqlang.github.io/jq/download/
```

### "curl command not found"
```bash
# Mac (should be pre-installed)
# If missing: xcode-select --install

# Linux
sudo apt-get install curl
```

### "Model not found" or "Invalid model"
- Check model name is exact (case-sensitive)
- Visit https://openrouter.ai/models to verify
- Some models require special access or credits

### Section generation fails or returns errors
- **Check OpenRouter credits:** Visit https://openrouter.ai/credits
- **Try different model:** Some models have rate limits
- **Enable debug mode:** `export VENTUREPULSE_DEBUG=1`
- **Check project file:** Ensure it's readable text/markdown

### Reports look broken or unstyled
- Open in modern browser (Chrome, Firefox, Safari, Edge)
- Check if HTML file is complete (not truncated)
- Try regenerating the section

### Analysis takes too long
- Expected: ~25 minutes for Quick Analysis (7 sections), ~60-90 minutes for Full Analysis (19 sections)
- Premium models (Claude) are slower but higher quality
- Try faster model: `google/gemini-2.0-flash-exp:free`

---

## 🗺️ Roadmap

### v2.1 (Current - December 2024)
- ✅ Expanded to 19 specialized sections (from 8)
- ✅ Streamlit web UI with multi-model comparison
- ✅ Quick (7 sections) / Full (19 sections) / Custom analysis modes
- ✅ Sequential and parallel model execution
- ✅ **Parallel section generation** - All sections generated simultaneously
- ✅ **Automatic retry logic** - Exponential backoff with jitter for failed API calls
- ✅ **Cost tracking** - Per-section and total costs in Provenance
- ✅ **Failure handling** - Graceful handling of partial failures with detailed error reporting
- ✅ Grouped section navigation (Foundation/Strategy/Execution/Future)
- ✅ Docker deployment support

### Future
- 🔄 Ollama/local model support
- 🔄 Ideas library for saved projects
- 🔄 Report export (PDF, combined HTML)

---

## 🤝 Contributing

Contributions welcome! Here's where we need help:

### High Priority
- **Prompt Engineering:** Improve section prompts for better insights
- **Industry Templates:** Create specialized prompts (fintech, healthcare, B2B SaaS, etc.)
- **Model Testing:** Test different models and report quality/cost findings
- **Documentation:** Improve guides, add tutorials, create videos

### Also Welcome
- **Bug Reports:** Find issues, suggest improvements
- **Feature Requests:** What would make this more useful?
- **Example Projects:** Contribute sample analyses
- **Translations:** Internationalize prompts and docs

Just open an issue or submit a PR on GitHub!

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

**TL;DR:** Use it, modify it, distribute it, commercialize it freely.

The generated reports are **yours**—use them however you want.

---

## 🙏 Acknowledgments

- Built with [OpenRouter](https://openrouter.ai) for unified multi-model AI access
- Inspired by months of real-world product validation experience
- Prompt refinement informed by 50+ test analyses
- Thanks to the open-source community

**Special thanks to early testers and contributors.**

---

## 📗 Links

- **GitHub:** https://github.com/knightsri/VenturePulse
- **Issues/Bugs:** https://github.com/knightsri/VenturePulse/issues
- **Discussions:** https://github.com/knightsri/VenturePulse/discussions
- **OpenRouter:** https://openrouter.ai
- **Model Directory:** https://openrouter.ai/models
- **Author Blog:** https://shalusri.com

---

## ❓ FAQ

### How much does it cost to run an analysis?

Depends on the model and analysis depth:

| Model | Quick (7 sections) | Full (19 sections) |
|-------|-------------------|-------------------|
| `deepseek/deepseek-chat` | ~$0.10-0.20 | ~$0.30-0.50 |
| `openai/gpt-4o-mini` | ~$0.10-0.25 | ~$0.30-0.60 |
| `meta-llama/llama-3.3-70b-instruct` | ~$0.20-0.40 | ~$0.50-1.00 |
| `mistralai/mistral-large` | ~$0.80-1.50 | ~$2-4 |
| `google/gemini-2.5-pro` | ~$1-2 | ~$3-5 |
| `openai/gpt-4o` | ~$1-2 | ~$3-6 |
| `anthropic/claude-3.5-sonnet` | ~$1.50-3 | ~$4-8 |
| `anthropic/claude-sonnet-4` | ~$2-4 | ~$5-10 |

**My workflow:** Start with **DeepSeek** or **GPT-4o-mini** to filter obviously flawed ideas quickly. For promising ideas, use **Claude Sonnet 4** or **Gemini 2.5 Pro** for investor-ready analysis. The Web UI shows exact cost per section and total in the Provenance report.

### How long does it take?

- **Quick Analysis:** ~25 minutes (7 core sections)
- **Full Analysis:** ~60-90 minutes (all 19 sections)
- Premium models are slower but produce higher quality analysis

Time varies by model—faster models complete quicker, premium models are slower but produce better analysis.

### Can I use this for commercial projects?

**Yes!** MIT license allows commercial use. The generated reports are yours to use however you want—pitch investors, share with clients, include in proposals, etc.

### How accurate is the analysis?

VenturePulse provides **strategic insights** based on AI reasoning and training data. It's exceptionally good at:
- ✅ Identifying competitive landscape
- ✅ Spotting risks you might miss
- ✅ Suggesting pricing strategies
- ✅ Structuring your thinking

**However, always:**
- Validate with domain experts
- Conduct your own customer research
- Verify competitive intelligence with primary sources
- Perform financial due diligence

**Think of it as:** A brilliant research assistant and strategic advisor, not a replacement for human judgment. It accelerates your thinking by 10x, but you still need to validate the insights.

### How does it compare to using ChatGPT/Claude directly?

**Using ChatGPT/Claude directly:**
- Generic, surface-level analysis
- Inconsistent structure across conversations
- You have to remember what to ask
- Missing critical dimensions
- No comparative framework
- Takes 2-3 weeks of iterating

**Using VenturePulse:**
- Comprehensive, structured analysis across 19 dimensions
- Proven framework covering all viability aspects
- Automatic competitive research
- Professional formatting with cost tracking
- Takes 25-90 minutes (vs. weeks manually)

**The prompts took months to refine.** You're getting battle-tested analysis templates that have been used on 50+ real projects.

### Can I customize the prompts?

**Absolutely!** That's the whole point of open-source. You can:
- Edit existing section prompts in `prompts/sections/`
- Add new sections (e.g., regulatory deep-dive for healthcare)
- Remove sections you don't need
- Adjust scoring criteria
- Change output format

Fork it and make it your own. Share improvements back with the community!

### Why separate HTML files instead of one big report?

**Strategic decision based on real-world use:**

**Advantages of separate files:**
- ✅ Share specific sections with different stakeholders
- ✅ Email just the "Executive Summary" to busy executives
- ✅ Regenerate individual sections without re-running everything
- ✅ Avoid token limit issues with complex projects
- ✅ Better quality—each section gets full AI focus

**Previous version** (one big file with tabs) had truncation issues and less detailed analysis.

**Future version** might include an optional "combined view" while keeping individual files.

### What if my idea is confidential?

**Your data never leaves your machine except for the API call to OpenRouter.** 

- API calls are encrypted (HTTPS)
- OpenRouter doesn't train on your data (per their policy)
- Generated reports are saved locally on your machine
- No telemetry, no tracking, no data collection by VenturePulse

**For extra security:**
- Use a self-hosted LLM (future feature)
- Review and redact your project file before analysis
- Check OpenRouter's privacy policy

### Can I run this offline or with local models?

**Not currently, but maybe in a future release:**
- Ollama integration for fully local analysis
- LM Studio support
- Self-hosted model options

For now, you need internet + OpenRouter API access.

### Why OpenRouter instead of direct API access?

**OpenRouter provides:**
- ✅ Single API key for 100+ models
- ✅ Unified pricing and billing
- ✅ Fallback routing if model is down
- ✅ Automatic load balancing
- ✅ Easy model switching
- ✅ Usage analytics

You *could* modify the scripts to call OpenAI/Anthropic/Google directly, but OpenRouter makes multi-model testing much easier.

### What if the analysis is wrong or misses something?

**AI analysis has limitations:**
- May miss recent market developments (post-training cutoff)
- Can't validate assumptions with real users
- Doesn't have your domain expertise
- May not know niche competitors

**How to use VenturePulse effectively:**
1. **Start:** Generate initial analysis
2. **Validate:** Check competitive research, verify claims
3. **Augment:** Add your domain knowledge and corrections
4. **Iterate:** Regenerate specific sections with more context
5. **Decide:** Use as input to your decision, not the sole factor

It's a **strategic thinking tool**, not a crystal ball.

---

## 🎯 Perfect For

- ✅ **Solo founders** validating side project ideas
- ✅ **Startup teams** exploring pivot opportunities
- ✅ **Product managers** assessing new feature viability
- ✅ **Consultants** scoping client projects
- ✅ **Investors** conducting preliminary due diligence
- ✅ **Students** learning product strategy frameworks
- ✅ **Agencies** evaluating build vs. buy decisions

---

## 🚀 Get Started

```bash
# 1. Clone the repo
git clone https://github.com/knightsri/VenturePulse.git
cd VenturePulse

# 2. Set your API key
export OPENROUTER_API_KEY="your_key_here"

# 3. Run the example
./analyze.sh examples/smartplate-idea.md

# 4. View the reports
cd smartplate-idea-analysis-*/
open executive-summary.html
```

**Stop spending weeks on viability analysis. Start building products faster.**

---

**Built by founders, for founders** 🚀  
**Built in public** 🌍  
**Built with AI** 🤖

Questions? Open an [issue](https://github.com/knightsri/VenturePulse/issues) or [discussion](https://github.com/knightsri/VenturePulse/discussions).
