
# 🎯 VenturePulse

> **AI-powered product viability analysis in minutes, not weeks**

Turn weeks of market research, competitive analysis, and strategic planning into a comprehensive AI-generated report suite in under 15 minutes.

---

## 🚀 What is VenturePulse?

VenturePulse is a **prompt library + CLI orchestrator** that generates McKinsey-quality product viability reports using AI. It analyzes your product idea across 9 critical dimensions, each as a standalone, focused HTML report:

1. **Executive Summary** - Viability scores, verdict, key highlights, recommended next steps
2. **Market Landscape** - Competitors, timing, TAM/SAM/SOM, white space analysis
3. **Technical Feasibility** - Architecture, complexity, AI/low-code implementation, risks  
4. **Competitive Advantage** - Moats, defensibility, competitive scoring matrix
5. **Business Model** - Pricing, unit economics, financial projections, compliance
6. **MVP Roadmap** - Feature prioritization matrix, phased timeline, implementation strategy
7. **Success Metrics** - KPIs across technical/engagement/business dimensions, risk register
8. **Go-to-Market** - ICP analysis, distribution channels, acquisition strategy
9. **Provenance & Metadata** - Analysis transparency, model details, generation timestamp

**The output:** Nine separate, beautifully formatted HTML reports—each independently comprehensive and presentation-ready.

---

## ✨ Why VenturePulse?

### The Old Way (2-3 weeks)
- ❌ 30+ fragmented AI conversations
- ❌ Manual research across competitors, pricing, tech stack
- ❌ Scattered insights in notes, docs, spreadsheets
- ❌ Missing critical dimensions (compliance, risks, defensibility)
- ❌ No structured decision framework

### The VenturePulse Way (10-15 minutes)
- ✅ One command generates 9 comprehensive reports
- ✅ Automated competitive research and market analysis
- ✅ Structured scoring across all viability dimensions
- ✅ Professional formatting ready for stakeholders/investors
- ✅ Costs $0 (free models) to $5 (premium analysis)

**What used to cost thousands in consulting fees now costs the price of a coffee.**

---

## ⚡ Quick Start

### Prerequisites

- Bash (Mac/Linux/WSL/Git Bash)
- `curl` and `jq` (`brew install jq` or `apt-get install jq`)
- [OpenRouter API key](https://openrouter.ai/keys) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/knightsri/VenturePulse.git
cd VenturePulse

# Make scripts executable
chmod +x analyze.sh scripts/*.sh

# Set your API key
export OPENROUTER_API_KEY="your_key_here"
```

### Run Your First Analysis

```bash
# Analyze the example project
./scripts/analyze.sh examples/sample-project/smartplate-idea.md

# View the reports (9 separate HTML files created)
cd examples/sample-project
cd smartplate-idea-analysis-claude-sonnet-4.5*
open index.html  # Start here!
```

**That's it!** You'll get all the comprehensive reports in 10-15 minutes.

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

VenturePulse works with 100+ models via [OpenRouter](https://openrouter.ai/models). Here are the best:

### ⭐ Best for VenturePulse

| Model | Speed | Quality | Cost/Report | Best For |
|-------|-------|---------|-------------|----------|
| `google/gemini-2.0-flash-exp:free` | ⚡⚡⚡ Fast | ✅ Good | 💰 **FREE** | Testing ideas quickly |
| `google/gemini-2.5-pro` | ⚡⚡ Medium | ✅✅ Excellent | 💰💰 ~$1-2 | Solid validation |
| `anthropic/claude-sonnet-4.5` | ⚡ Slower | ✅✅✅ **Best** | 💰💰💰 ~$3-5 | Investor-ready analysis |
| `deepseek/deepseek-chat` | ⚡⚡⚡ Fast | ✅ Decent | 💰 ~$0.10 | High-volume testing |

**My recommendation:** Start with **free models** to filter bad ideas. For ideas that pass initial validation, use **Claude Sonnet 4.5**—the depth is worth every penny.

**See all models:** https://openrouter.ai/models

---

## 📁 Project Structure

```
VenturePulse/
├── analyze.sh                          # Main CLI orchestrator
├── prompts/
│   ├── common-instructions.md          # Shared analysis guidelines
│   └── sections/
│       ├── section01-executive-summary.md
│       ├── section02-market-landscape.md
│       └── ... (9 total section prompts)
├── scripts/
│   ├── call-openrouter.sh             # OpenRouter API wrapper
│   ├── create-wrapper.sh              # HTML generation & styling
│   └── generate-provenance.sh         # Metadata generation
├── examples/
│   └── sample-project/
│       ├── smartplate-idea.md             # Sample project description
│       └── smartplate-idea-analysis-*/    # Sample generated reports
└── README.md
```

---

## 💡 How It Works

### The Architecture

**Previous approach (v1.0):** Single mega-prompt → One massive 9-tab HTML page
- ❌ Token limits with complex ideas
- ❌ Inconsistent output quality
- ❌ Harder to regenerate individual sections

**Current approach (v1.5):** Sequential specialized prompts → all focused HTML reports by section
- ✅ Each analysis builds on previous insights
- ✅ More reliable, more detailed outputs
- ✅ Easy to regenerate any individual report
- ✅ Better handling of complex projects

### The Process

1. **You provide:** A markdown/text file describing your product idea (1-3 pages ideal)

2. **VenturePulse orchestrates:**
   - Loads common analysis instructions
   - Sequentially generates 9 specialized reports:
     - Each section calls OpenRouter API with your chosen model
     - Later sections reference insights from earlier reports
     - Each generates its own styled HTML file
   - Creates provenance metadata for transparency

3. **You get:** all comprehensive HTML reports in a timestamped folder

**Total time:** 10-15 minutes (varies by model)
**Total cost:** $0 (free) to $5 (premium)

---

## 🎨 What You Get

### Report Structure

Each analysis creates **separate HTML files** in a timestamped folder:

```
my-idea-analysis-model-20241021-143052/
├── index.html          ⭐ Start here
├── market-landscape.html
├── technical-feasibility.html
├── competitive-advantage.html
├── business-model.html
├── mvp-roadmap.html
├── success-metrics.html
├── go-to-market.html
└── provenance-metadata.html
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

**...and 6 more equally detailed reports.**

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
- Get clear go/no-go decision in 15 minutes vs. 2 weeks of research

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

### Set Default Model

Edit `analyze.sh`:
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
- Expected: 10-15 minutes for 9 reports
- Premium models (Claude) are slower but higher quality
- Try faster model: `google/gemini-2.0-flash-exp:free`

---

## 🗺️ Roadmap

### v1.5 (Current - October 2024)
- ✅ Sequential specialized prompts (9 separate reports)
- ✅ Each section builds on previous insights
- ✅ Improved reliability and depth
- ✅ Better handling of complex projects

TBD

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

**TL;DR:** Use it, modify it, distribute it, commercialize it. Just include the license file.

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

Depends on the model you choose:

| Model | Cost per Full Analysis |
|-------|----------------------|
| `google/gemini-2.0-flash-exp:free` | **$0** (currently free) |
| `deepseek/deepseek-chat` | ~$0.10-0.20 |
| `google/gemini-2.5-pro` | ~$1-2 |
| `anthropic/claude-sonnet-4.5` | ~$3-5 |

**My workflow:** Start with free model ($0) to filter obviously flawed ideas. For promising ideas, use Claude Sonnet 4.5 ($3-5) for investor-ready analysis.

### How long does it take?

- **Currently:** 10-15 minutes (sequential generation of 9 reports)
- **Coming soon:** 3-5 minutes (parallel generation in v1.6)

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
- Comprehensive, structured analysis
- Proven framework covering all dimensions
- Automatic competitive research
- Professional formatting
- Takes 10-15 minutes

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
