.PHONY: install test test-verbose lint build run clean

install:
	pip install -r requirements.txt
	pip install pytest

test:
	python -m pytest tests/ -v

test-mapping:
	python -m pytest tests/test_transform.py -v

test-diff:
	python -m pytest tests/test_diff.py -v

build:
	docker build -t seeder .

run:
	cd src && python main.py

run-docker:
	docker run --env-file .env seeder

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
