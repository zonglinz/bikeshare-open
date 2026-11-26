# Bikeshare demand capstone

Reference repository for the DSC 180A methodology lesson on agentic
programming. Forecasts daily Capital Bikeshare ridership (`cnt`) for
Washington, DC, 2011-2012, with a leakage trap in the data.

The agent is Claude Code driving an **open-weight model running on your own
machine** through Ollama. No Anthropic account, subscription, or API key is
needed. Nothing leaves your laptop.

## Setup

Use Python 3.13 (3.12+ is required by the starter's NumPy 2.5.3 pin).
The original Python 3.11 setup cannot install those pins.


    # 1. Ollama (the local model server)   https://ollama.com/download
    ollama serve                           # leave running in its own terminal

    # 2. Claude Code (the agent harness; free to install, no login needed here)
    curl -fsSL https://claude.ai/install.sh | bash

    # 3. This repo
    python3.13 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    make model          # pulls the base model, builds `bikeshare-coder` with a 64k context
    make check-model    # confirms Claude Code can reach it and that tool calls work
    make all            # data -> features -> train, writes reports/metrics.json
    make test           # includes feature, schema and integrity guards

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

## Assignment additions

`REPORT.md` contains the required five sections and the eight-row table.
The three-day mean candidate is implemented and tested, but excluded from
selected inputs after negative validation deltas. `reports/metrics.json`
contains `before_feature` and `after_feature`; its top-level models select
`before_feature`. The target-change experiment is reported in separate
JSON files, preserving untransformed headline metrics.

The custom `/seed-fault <forbidden|rolling|weather|raw-bash>` skill and
`python tools/seed_fault.py <name>` capture actual tests and hook stderr in
disposable copies. `docs/SEEDED_FAULTS.md` contains the transcripts.
`make data` checks the immutable raw hash, including changes made by Bash.
`make test` uses validation for routine model-quality assertions.

Run the batch auditor after `make all`:

    python agent/audit.py . --out reports/audit.jsonl

It uses the local model configured in `.claude/settings.json`; read-only
model tools are supplemented by deterministic identity and fresh-copy
pipeline checks. A failed model reply produces an explicit error row;
one repository failure does not discard the batch. Full model/tool output
is saved in `reports/audit-transcript.jsonl`.

Exercise 3's teammate audit is complete for AhmadAgeel/bikeshare-open at
commit a2192434d64add5b5cb2c7b4008e4ae58c66a3b5. See `docs/AUDIT.md` and
`reports/peer-review/` for the real reviewer output, checks and assessment.
The public repository is https://github.com/zonglinz/bikeshare-open.
Review the proposed decisions and attribution, then submit that URL through
the course form. No course submission has been sent by the agent.

### Recorded local audit runtime

The recorded review uses `qwen3.5:0.8b-q8_0` (752.39M text parameters),
64k context, temperature 0, CPU inference, Ollama 0.40.18, and the CLI
bundled with the pinned SDK. The original default model recipe remains
available; `model/Modelfile.audit` records this smaller review build.
The author's Codex model and this local reviewer are distinct.

To repeat that local review setup, run a CPU server in one terminal:

    LLAMA_ARG_DEVICE=none LLAMA_ARG_N_GPU_LAYERS=0 LLAMA_ARG_MMPROJ_OFFLOAD=0 MTMD_BACKEND_DEVICE=none ollama serve

Then, in the activated project environment:

    ollama pull qwen3.5:0.8b-q8_0
    ollama create bikeshare-coder -f model/Modelfile.audit
    make check-model
    python agent/audit.py . --out reports/audit.jsonl

CPU mode avoids the Metal command-queue failure observed inside the Codex
sandbox. Original failed readiness logs and the corrected successful run
are retained under `reports/model-*.txt`; `reports/model-info.json` records
the actual source weights and runtime. The pipeline itself runs offline
with `make all` and does not require the agent model.
