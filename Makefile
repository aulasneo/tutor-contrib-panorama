.DEFAULT_GOAL := help
.PHONY: docs requirements upgrade

PYTHON ?= python3
SRC_DIRS = ./tutorpanorama
BLACK_OPTS = --exclude templates ${SRC_DIRS}

clean: ## Remove build artifacts
	rm -rf build dist *.egg-info

upgrade: ## Upgrade project and development dependencies from pyproject.toml
	$(PYTHON) -m pip install --upgrade --upgrade-strategy eager -e '.[dev]'

requirements: ## Install project and development dependencies from pyproject.toml
	$(PYTHON) -m pip install --upgrade -e '.[dev]'

build: clean ## Build the package
	$(PYTHON) -m build

dist: ## Upload package to PyPI
	twine upload dist/*

test: test-lint test-types test-format test-dist test-tutor test-unit test-navigation ## Run static, packaging, Python, and navigation checks.

test-format: ## Run code formatting tests
	black --check --diff $(BLACK_OPTS)

test-lint: ## Run code linting tests
	pylint --errors-only --enable=unused-import,unused-argument --ignore=templates --ignore=docs/_ext ${SRC_DIRS}

test-types: ## Run type checks.
	mypy --exclude=templates --ignore-missing-imports --implicit-reexport --strict ${SRC_DIRS}

test-dist: build ## Check the distribution files
	twine check dist/*

test-tutor:
	export TUTOR_ROOT=$$(mktemp -d); trap 'rm -rf "$$TUTOR_ROOT"' EXIT; \
		tutor plugins enable mfe panorama && tutor config save

test-unit: ## Run Python contract tests
	$(PYTHON) -m pytest tests

test-navigation: ## Test navigation and parse the generated combined MFE configuration
	npm ci --ignore-scripts
	export TUTOR_ROOT=$$(mktemp -d); trap 'rm -rf "$$TUTOR_ROOT"' EXIT; \
		tutor plugins enable mfe panorama && tutor config save && \
		PANORAMA_GENERATED_ENV="$$TUTOR_ROOT/env/plugins/mfe/build/mfe/env.config.jsx" node --test tests/navigation.cjs

format: ## Format code automatically
	black $(BLACK_OPTS)

isort: ##  Sort imports. This target is not mandatory because the output may be incompatible with black formatting. Provided for convenience purposes.
	isort --skip=templates ${SRC_DIRS}

ESCAPE = 
help: ## Print this help
	@grep -E '^([a-zA-Z_-]+:.*?## .*|######* .+)$$' Makefile \
		| sed 's/######* \(.*\)/@               $(ESCAPE)[1;31m\1$(ESCAPE)[0m/g' | tr '@' '\n' \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'
