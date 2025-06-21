# Makefile for Quotient project

.PHONY: help test scripts-% api frontend

help:
	@echo "Available make commands:"
	@echo "  make test             - Run all Python test scripts in scripts/"
	@echo "  make scripts-<name>   - Run a specific test script (e.g., make scripts-test_api)"
	@echo "  make api              - Start the FastAPI server (api.py)"
	@echo "  make frontend         - Start the React frontend (Vite dev server)"

# Run all test scripts
TESTS := $(wildcard scripts/test_*.py)

test:
	@for t in $(TESTS); do echo "Running $$t"; python3 $$t || exit 1; done

# Run a specific test script: make scripts-test_api
# Usage: make scripts-test_api
# This will run scripts/test_api.py
scripts-%:
	python3 scripts/$*.py

# Start the FastAPI server
api:
	python3 api.py

# Start the React frontend
frontend:
	cd frontend && npm run dev
