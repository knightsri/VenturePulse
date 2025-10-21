#!/bin/bash
# analyze.sh - VenturePulse Report Generator v1.0

set -e

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check OPENROUTER_API_KEY or set a default key here
if [ -z "$OPENROUTER_API_KEY" ]; then
  export OPENROUTER_API_KEY="sk-orv....your-key-goes-here...."
fi

# Default model (free and fast) - use any of these
DEFAULT_MODEL="deepseek/deepseek-r1-0528-qwen3-8b:free"
#DEFAULT_MODEL="tngtech/deepseek-r1t2-chimera:free"

# Show usage
show_usage() {
    cat << EOF
VenturePulse - AI-Powered Product Viability Analysis

Usage: $0 <project-file> [model]

Arguments:
  project-file    Path to your project description (markdown or text)
  model          OpenRouter model to use (optional, default: $DEFAULT_MODEL)

Examples:
  $0 my-idea.md
  $0 my-idea.md anthropic/claude-sonnet-4
  $0 my-idea.md deepseek/deepseek-chat

Popular Models:
  google/gemini-2.0-flash-exp:free    Fast, FREE (recommended for testing)
  google/gemini-pro-1.5               Balanced quality/cost
  anthropic/claude-sonnet-4           Best quality
  openai/gpt-4-turbo                  Industry standard
  deepseek/deepseek-chat              Cheapest paid option (\$0.14/1M tokens)

See all models: https://openrouter.ai/models

Environment:
  OPENROUTER_API_KEY    Required - Get yours at https://openrouter.ai/keys
  VENTUREPULSE_DEBUG    Optional - Set to 1 for debug output

EOF
}

# Check arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

PROJECT_FILE="$1"
MODEL="${2:-$DEFAULT_MODEL}"
MODEL_NAME=$(echo "$MODEL" | sed -E 's/^[^\/]*\///; s/[^A-Za-z0-9_]/-/g; s/[-_][-_]*/-/g')

# Validate project file exists
if [ ! -f "$PROJECT_FILE" ]; then
    echo -e "${RED}Error: Project file not found: $PROJECT_FILE${NC}" >&2
    exit 1
fi

# Generate output directory name
PROJECT_NAME=$(basename "$PROJECT_FILE" | sed 's/\.[^.]*$//' | sed 's/[^a-zA-Z0-9-]/-/g' | tr '[:upper:]' '[:lower:]')
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_DIR="${PROJECT_NAME}-analysis-${MODEL_NAME}-${TIMESTAMP}"

# Header
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎯 VenturePulse Analysis v1.0${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Project:    $PROJECT_NAME"
echo "Model:      $MODEL"
echo "Output:     $OUTPUT_DIR"
echo ""

# Check API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}Error: OPENROUTER_API_KEY environment variable not set${NC}" >&2
    echo "" >&2
    echo "Get your API key at: https://openrouter.ai/keys" >&2
    echo "Then run: export OPENROUTER_API_KEY='your_key_here'" >&2
    echo "" >&2
    exit 1
fi

# Check dependencies
for cmd in jq curl; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: Required command '$cmd' not found${NC}" >&2
        echo "Install it with: brew install $cmd  (or apt-get install $cmd)" >&2
        exit 1
    fi
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Read project data
PROJECT_DATA=$(cat "$PROJECT_FILE")

# Load common instructions
if [ ! -f "prompts/common-instructions.md" ]; then
    echo -e "${RED}Error: prompts/common-instructions.md not found${NC}" >&2
    exit 1
fi
COMMON_INSTRUCTIONS=$(cat "prompts/common-instructions.md")

# Section definitions: 
#    number:display-name:file-slug
declare -a SECTIONS=(
    "01:Executive Summary:executive-summary"
    "02:Market Landscape:market-landscape"
    "03:Technical Feasibility:technical-feasibility"
    "04:Competitive Advantage:competitive-advantage"
    "05:Business Model:business-model"
    "06:MVP Roadmap:mvp-roadmap"
    "07:Success Metrics:success-metrics"
    "08:Go-to-Market:go-to-market"
)


# Generate sections
echo -e "${BLUE}Generating sections...${NC}"
echo ""

for SECTION_DEF in "${SECTIONS[@]}"; do
    IFS=':' read -r NUM NAME SLUG <<< "$SECTION_DEF"
    
    echo -e "${GREEN}📝 Section ${NUM}: ${NAME}${NC}"
    
    # Check if section prompt exists
    PROMPT_FILE="prompts/sections/section${NUM}-${SLUG}.md"
    if [ ! -f "$PROMPT_FILE" ]; then
        echo -e "${YELLOW}   ⚠️  Warning: $PROMPT_FILE not found, skipping...${NC}"
        continue
    fi
    
    # Load section prompt
    SECTION_PROMPT=$(cat "$PROMPT_FILE")
    
    # Build full prompt
    FULL_PROMPT="${COMMON_INSTRUCTIONS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${SECTION_PROMPT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PROJECT DATA

${PROJECT_DATA}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate the HTML for this section now."
    
    # Output file
    OUTPUT_FILE="$OUTPUT_DIR/section${NUM}-${SLUG}.html"
    
    # Call OpenRouter (with error handling)
    if ./scripts/call-openrouter.sh "$MODEL" "$FULL_PROMPT" > "$OUTPUT_FILE" 2>&1; then
        WORD_COUNT=$(wc -w < "$OUTPUT_FILE" | tr -d ' ')
        echo -e "   ✅ Generated: section${NUM}-${SLUG}.html (${WORD_COUNT} words)"
    else
        echo -e "${RED}   ❌ Failed to generate Section ${NUM}${NC}" >&2
        echo -e "${RED}   Check error output above for details${NC}" >&2
        exit 1
    fi
    
    # Small delay to avoid rate limits (adjust if needed)
    sleep 0.5
done

# Generate provenance section (no AI needed)
echo ""
echo -e "${GREEN}📝 Section 09: Provenance${NC}"
if ./scripts/generate-provenance.sh "$PROJECT_NAME" "$MODEL" > "$OUTPUT_DIR/section09-provenance.html"; then
    echo -e "   ✅ Generated: section09-provenance.html"
else
    echo -e "${YELLOW}   ⚠️  Warning: Failed to generate provenance${NC}"
fi

# Create wrapper HTML
echo ""
echo -e "${GREEN}🎨 Creating report wrapper...${NC}"
if ./scripts/create-wrapper.sh "$PROJECT_NAME" "$OUTPUT_DIR"; then
    echo -e "   ✅ Created: index.html"
else
    echo -e "${RED}   ❌ Failed to create wrapper${NC}" >&2
    exit 1
fi

# Success message
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Analysis Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Report saved to: $OUTPUT_DIR/"
echo ""
echo "To view the report:"
echo -e "  ${BLUE}open $OUTPUT_DIR/index.html${NC}"
echo ""
echo "Or start a local server:"
echo -e "  ${BLUE}cd $OUTPUT_DIR && python3 -m http.server 8000${NC}"
echo "  Then open: http://localhost:8000"
echo ""
