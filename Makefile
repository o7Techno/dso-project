.PHONY: help build up down logs test lint scan clean check-user check-health

help:
	@echo "Available targets:"
	@echo "  make build        - Build Docker image"
	@echo "  make up           - Start services with docker compose"
	@echo "  make down         - Stop services"
	@echo "  make logs          - Show logs"
	@echo "  make test          - Run tests in container"
	@echo "  make lint          - Run Hadolint on Dockerfile"
	@echo "  make scan          - Run Trivy security scan"
	@echo "  make check-user    - Check that container runs as non-root"
	@echo "  make check-health  - Check container health status"
	@echo "  make clean         - Clean up containers and images"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

test:
	docker compose run --rm app python -m pytest -q

lint:
	@echo "Running Hadolint on Dockerfile..."
	@if command -v hadolint >/dev/null 2>&1; then \
		hadolint Dockerfile; \
	else \
		echo "Hadolint not found. Install with: brew install hadolint (macOS) or see https://github.com/hadolint/hadolint"; \
		docker run --rm -i hadolint/hadolint < Dockerfile; \
	fi

scan:
	@echo "Running Trivy security scan..."
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image dso-project-app:latest 2>/dev/null || (docker compose build && trivy image dso-project-app:latest); \
	else \
		echo "Trivy not found. Using Docker image..."; \
		docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
			-v $$PWD:/workspace aquasec/trivy:latest image dso-project-app:latest || \
			(docker compose build && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
			-v $$PWD:/workspace aquasec/trivy:latest image dso-project-app:latest); \
	fi

check-user:
	@echo "Checking container user..."
	@docker compose run --rm app id -u | grep -v "^0$$" && echo "✓ Container runs as non-root" || (echo "✗ Container runs as root!" && exit 1)

check-health:
	@echo "Checking container health..."
	@timeout=60; \
	while [ $$timeout -gt 0 ]; do \
		health=$$(docker inspect --format='{{.State.Health.Status}}' event-planner-app 2>/dev/null || echo "starting"); \
		if [ "$$health" = "healthy" ]; then \
			echo "✓ Container is healthy"; \
			exit 0; \
		fi; \
		echo "Waiting for container to become healthy... ($$health)"; \
		sleep 5; \
		timeout=$$((timeout-5)); \
	done; \
	echo "✗ Container did not become healthy within timeout"; \
	exit 1

clean:
	docker compose down -v
	docker rmi dso-project-app:latest 2>/dev/null || true
