.PHONY: dev test lint format check clean

# ── Backend ──────────────────────────────────────────────────────────

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --tb=short

lint:
	flake8 app/ tests/ --max-line-length 120 --extend-ignore E501,W503
	bandit -r app/ --severity-level high

format:
	black app/ tests/ --line-length 100

format-check:
	black --check app/ tests/ --line-length 100

check: format-check lint test

# ── Frontend ─────────────────────────────────────────────────────────

fe-dev:
	npm run dev

fe-test:
	npm test

fe-lint:
	npm run lint

fe-build:
	npm run build

# ── Infrastructure ───────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	rm -rf dist/ build/ coverage/ reports/ .cache/
