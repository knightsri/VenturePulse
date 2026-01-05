#!/bin/bash
# scripts/call-openrouter.sh - OpenRouter API wrapper with timing instrumentation

set -e

# Check arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <model> <prompt>" >&2
    exit 1
fi

MODEL="$1"
PROMPT="$2"

VENTUREPULSE_DEBUG=""
VENTUREPULSE_TIMING=""


# Start total timing (milliseconds)
TOTAL_START=$(date +%s)

# Check for API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Error: OPENROUTER_API_KEY environment variable not set" >&2
    echo "" >&2
    echo "Get your key at: https://openrouter.ai/keys" >&2
    echo "Then run: export OPENROUTER_API_KEY='your_key_here'" >&2
    exit 1
fi

# Time: Creating request body
REQUEST_START=$(date +%s)

# Create temporary file for request body
TEMP_REQUEST=$(mktemp)
trap "rm -f $TEMP_REQUEST" EXIT

# Build JSON request (using jq for proper escaping)
cat > "$TEMP_REQUEST" << EOF
{
    "model": "$MODEL",
    "messages": [
        {
            "role": "user",
            "content": $(echo "$PROMPT" | jq -Rs .)
        }
    ],
    "max_tokens": 25192,
    "temperature": 0.7,
    "top_p": 0.95
}
EOF

REQUEST_END=$(date +%s)
REQUEST_TIME=$((REQUEST_END - REQUEST_START))

# Time: API call
API_START=$(date +%s)

# Call OpenRouter API
RESPONSE=$(curl -s https://openrouter.ai/api/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
    -H "HTTP-Referer: https://github.com/knightsri/VenturePulse" \
    -H "X-Title: VenturePulse CLI v1.0" \
    -d @"$TEMP_REQUEST")

API_END=$(date +%s)
API_TIME=$((API_END - API_START))

# Time: Response parsing
PARSE_START=$(date +%s)

# Check for API errors
if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    ERROR_TYPE=$(echo "$RESPONSE" | jq -r '.error.code // "unknown"')
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // "Unknown error"')
    
    echo "Error from OpenRouter API:" >&2
    echo "  Type: $ERROR_TYPE" >&2
    echo "  Message: $ERROR_MSG" >&2
    
    # Provide helpful hints for common errors
    case $ERROR_TYPE in
        "invalid_api_key")
            echo "" >&2
            echo "Hint: Check that your OPENROUTER_API_KEY is correct" >&2
            echo "Get a key at: https://openrouter.ai/keys" >&2
            ;;
        "insufficient_quota")
            echo "" >&2
            echo "Hint: Add credits to your OpenRouter account" >&2
            echo "https://openrouter.ai/credits" >&2
            ;;
        "model_not_found")
            echo "" >&2
            echo "Hint: Check available models at: https://openrouter.ai/models" >&2
            ;;
    esac
    
    exit 1
fi

# Check if response has choices
if ! echo "$RESPONSE" | jq -e '.choices[0]' > /dev/null 2>&1; then
    echo "Error: Unexpected API response format" >&2
    echo "Response: $RESPONSE" >&2
    exit 1
fi

# Extract and output the content
echo "$RESPONSE" | jq -r '.choices[0].message.content'

PARSE_END=$(date +%s)
PARSE_TIME=$((PARSE_END - PARSE_START))

# Total time
TOTAL_END=$(date +%s)
TOTAL_TIME=$((TOTAL_END - TOTAL_START))

# Log timing breakdown (to stderr so it doesn't pollute output)
if [ -n "$VENTUREPULSE_DEBUG" ] || [ -n "$VENTUREPULSE_TIMING" ]; then
    echo "⏱️  Timing Breakdown:" >&2
    echo "   Request build:  ${REQUEST_TIME}s" >&2
    echo "   API call:       ${API_TIME}s" >&2
    echo "   Response parse: ${PARSE_TIME}s" >&2
    echo "   TOTAL:          ${TOTAL_TIME}s" >&2
fi

# Also log usage statistics if available
if [ -n "$VENTUREPULSE_DEBUG" ]; then
    USAGE=$(echo "$RESPONSE" | jq -r '.usage // empty')
    if [ -n "$USAGE" ]; then
        echo "📊 Token usage: $USAGE" >&2
    fi
fi