.PHONY: all data features train test clean model check-model
.NOTPARALLEL: all
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
export OMP_NUM_THREADS = 1
export OPENBLAS_NUM_THREADS = 1
export LOKY_MAX_CPU_COUNT = 1

# --- The pipeline ----------------------------------------------------------
all: data features train

data:
	$(PYTHON) -m src.ingest

features:
	$(PYTHON) -m src.features

train:
	$(PYTHON) -m src.train

test:
	$(PYTHON) -m pytest tests/ -q

clean:
	rm -f data/processed/*.parquet reports/metrics.json reports/*.png

# --- The agent model (open weights, local) ----------------------------------
# Builds `bikeshare-coder`: the base model plus a 64k context window, which
# Claude Code needs and Ollama does not give you by default. Pick a larger
# BASE if your machine has the memory (see README.md).
BASE ?= qwen3.5:9b

model:
	ollama pull $(BASE)
	@set -e; model_recipe_file=$$(mktemp); \
	trap 'rm -f "$$model_recipe_file"' EXIT; \
	sed "s|^FROM .*|FROM $(BASE)|" model/Modelfile > "$$model_recipe_file"; \
	ollama create bikeshare-coder -f "$$model_recipe_file"

check-model:
	bash model/check.sh
