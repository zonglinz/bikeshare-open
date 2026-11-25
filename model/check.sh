#!/usr/bin/env bash
# `make check-model`: is the local agent model ready for Claude Code?
# Exits non-zero with a plain explanation if not. Run this before `claude`.
set -uo pipefail

MODEL="${MODEL:-bikeshare-coder}"
HOST="${OLLAMA_HOST:-http://localhost:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "FAIL: ollama is not installed. See https://ollama.com/download" >&2; exit 1
fi
if ! curl -fsS "$HOST/api/tags" >/dev/null 2>&1; then
  echo "FAIL: no Ollama server at $HOST. Start it with: ollama serve" >&2; exit 1
fi
if ! model_info=$(ollama show "$MODEL" 2>/dev/null); then
  echo "FAIL: model '$MODEL' not built. Run: make model" >&2; exit 1
fi

ctx=$(awk '/num_ctx/ {print $2; exit}' <<< "$model_info")
if [ -z "$ctx" ] || [ "$ctx" -lt 65536 ]; then
  echo "FAIL: '$MODEL' has num_ctx=${ctx:-unset}; need >= 65536. Rebuild with: make model" >&2; exit 1
fi
if ! grep -qi "tools" <<< "$model_info"; then
  echo "WARN: '$MODEL' does not advertise tool support; Claude Code needs it." >&2
fi

# One real request through the Anthropic-compatible endpoint, with a tool,
# so a broken install fails here and not twenty minutes into Step 2.
resp=$(curl -fsS "$HOST/v1/messages" \
  -H "content-type: application/json" -H "x-api-key: ollama" -H "anthropic-version: 2023-06-01" \
  -d "{\"model\":\"$MODEL\",\"max_tokens\":256,\"thinking\":{\"type\":\"disabled\"},\"tools\":[{\"name\":\"ping\",\"description\":\"Reply by calling this tool.\",\"input_schema\":{\"type\":\"object\",\"properties\":{}}}],\"messages\":[{\"role\":\"user\",\"content\":\"Call the ping tool.\"}]}" 2>&1)
if ! python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if any(b.get("type")=="tool_use" and b.get("name")=="ping" for b in d.get("content",[])) else 1)' <<< "$resp"; then
  echo "FAIL: the model did not complete a tool call." >&2
  echo "      raw: $(printf '%s' "$resp" | head -c 300)" >&2
  exit 1
fi

echo "OK model: $MODEL at $HOST, num_ctx=$ctx, tool call works."
