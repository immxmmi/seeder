.PHONY: help install test test-mapping test-diff test-config test-integration build run run-debug run-example run-docker clean

help:
	@echo "Available targets:"
	@echo "  install      Install dependencies"
	@echo "  test         Run full test suite"
	@echo "  test-mapping Run mapping tests"
	@echo "  test-diff    Run diff tests"
	@echo "  test-config  Run config loader tests"
	@echo "  build        Build Docker image"
	@echo "  run          Run seeder"
	@echo "  run-debug    Run seeder with debug logging"
	@echo "  run-example  Run seeder with example settings"
	@echo "  run-docker   Run Docker image with .env"
	@echo "  clean        Remove caches"

install:
	pip install -r requirements.txt
	pip install pytest

test:
	python -m pytest tests/ -v

test-mapping:
	python -m pytest tests/test_transform.py -v

test-diff:
	python -m pytest tests/test_diff.py -v

test-config:
	python -m pytest tests/test_config_loader.py -v

test-integration:
	RUN_INTEGRATION_TESTS=true python -m pytest tests/test_integration.py -v

build:
	docker build -t seeder .

run:
	cd src && python main.py

run-debug:
	cd src && DEBUG_ENABLED=true python main.py

run-example:
	cd src && SEEDER_CONFIG_FILE=config/settings.example.yaml python main.py

run-docker:
	docker run --env-file .env seeder

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
