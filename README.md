# Bikeshare demand capstone

Reference repository for the DSC 180A methodology lesson on agentic
programming. Forecasts daily Capital Bikeshare ridership (`cnt`) for
Washington, DC, 2011-2012, with a leakage trap in the data.

The agent is Claude Code driving an **open-weight model running on your own
machine** through Ollama. No Anthropic account, subscription, or API key is
needed. Nothing leaves your laptop.

## Setup

    # 1. Ollama (the local model server)   https://ollama.com/download
    ollama serve                           # leave running in its own terminal

    # 2. Claude Code (the agent harness; free to install, no login needed here)
    curl -fsSL https://claude.ai/install.sh | bash

    # 3. This repo
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    make model          # pulls the base model, builds `bikeshare-coder` with a 64k context
    make check-model    # confirms Claude Code can reach it and that tool calls work
    make all            # data -> features -> train, writes reports/metrics.json
    make test           # 14 tests

    # 4. Start the agent, from the repo root
    claude

`.claude/settings.json` points Claude Code at `http://localhost:11434` and
names the model, so `claude` works with no environment variables. Run
`/status` inside Claude Code to confirm it says `bikeshare-coder`.

### Which base model

`make model` builds from `qwen3.5:9b` by default. Pick by memory:

| Your machine | Base model | `make model` command |
|---|---|---|
| 16 GB RAM (any laptop) | `qwen3.5:9b` (~7 GB) | `make model` |
| 32 GB RAM, or 24 GB+ Apple Silicon | `qwen3.5:27b` (~18 GB) | `make model BASE=qwen3.5:27b` |
| 48 GB+ | `qwen3.5:35b` (~22 GB) | `make model BASE=qwen3.5:35b` |
| Under 16 GB, or no patience | a hosted model, below | — |

The 64k context window adds several GB on top of the download size at run
time. If the model runs but is painfully slow, drop a size, not the context.
Any tool-capable model from the Ollama library works; the lesson does not
depend on this one. Record which model you used in `REPORT.md`.

### If your laptop cannot run a model

Ollama can serve the same models from its cloud, and Claude Code can point at
any endpoint that speaks the Anthropic Messages API. Override the repo
settings in `.claude/settings.local.json` (git-ignored) rather than editing
`settings.json`:

    {
      "model": "qwen3.5:27b-cloud",
      "env": {
        "ANTHROPIC_BASE_URL": "https://ollama.com",
        "ANTHROPIC_AUTH_TOKEN": "<your Ollama API key>",
        "ANTHROPIC_API_KEY": ""
      }
    }

Model names and free-tier limits for hosted models change; check
`ollama.com/search?c=cloud` for what is current. A paid Anthropic plan also
works, with `"env": {}` to clear the override, and is the only setup in
which `model: opus` or `sonnet` names mean anything.

## Data

Daily aggregation of the UCI Bike Sharing Dataset (Fanaee-T and Gama, 2013),
via the processed mirror used in Molnar's *Interpretable Machine Learning*:

    https://raw.githubusercontent.com/christophM/interpretable-ml-book/master/data/bike.csv

The mirror differs from the UCI file. See `src/config.py` for the list.
`data/raw/bike_daily.csv` is a checked-in copy so the pipeline runs offline;
it is immutable (writes are denied in `.claude/settings.json`).

`python -m src.leakage_demo` reproduces the R^2 = 1.000 result from the lesson.

## Layout

See `CLAUDE.md` for the standing rules and `src/config.py` for every constant.
`.claude/` holds the hook, permissions, reviewer subagent and `new-feature`
skill the lesson builds in Steps 7-8. `model/` holds the Modelfile and the
readiness check. `agent/audit.py` is the Agent SDK batch auditor from Part 4;
it uses the same local endpoint (`AUDIT_MODEL` overrides the model). Record
methodological decisions in `docs/DECISIONS.md`.
