.PHONY: help setup-dev test test-fast smoke ci-test demo compare clean-artifacts reset-env

export PYTHONPATH := $(shell pwd)

help:
	@echo "AetherNet MVP Makefile Commands:"
	@echo "  make help            - Show this help message"
	@echo "  make setup-dev       - Install developer dependencies in the current environment"
	@echo "  make smoke           - Run a fast sanity check (demo + fail-fast tests) before pushing"
	@echo "  make test            - Run the full pytest test suite"
	@echo "  make test-fast       - Run tests, stopping on first failure"
	@echo "  make ci-test         - Run tests for CI pipeline"
	@echo "  make demo            - Run the default multi-hop simulation scenario"
	@echo "  make compare         - Run all built-in scenarios and generate comparison report"
	@echo "  make clean-artifacts - Safely delete generated reports from artifacts/"
	@echo "  make reset-env       - Reset payload directories to a clean state"

setup-dev:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements-dev.txt
	@echo "Developer dependencies installed."

smoke: demo test-fast
	@echo "Smoke test passed! Ready to push."

test:
	pytest tests/ -v

test-fast:
	pytest tests/ -x -v

ci-test: test

demo:
	./scripts/run_demo.sh

compare:
	./scripts/run_compare.sh

clean-artifacts:
	rm -rf artifacts/reports
	rm -f artifacts/comparison.json
	@mkdir -p artifacts/reports
	@echo "Artifacts cleaned."

reset-env:
	./scripts/reset_env.sh