.PHONY: up down test test-all frontend-test logs build

up:            ## Start the full local stack
	docker compose up --build -d

down:          ## Stop and remove the local stack
	docker compose down -v

logs:          ## Tail logs from all services
	docker compose logs -f

test-all:      ## Run unit tests for every microservice + the API gateway
	@for svc in auth-service patient-service doctor-service appointment-service \
	            medical-records-service billing-service notification-service reporting-service \
	            api-gateway; do \
		echo "=== $$svc ==="; \
		cd services/$$svc && ([ -d ../../shared/common ] && cp -r ../../shared/common ./shared_common || true) && \
		PYTHONPATH=. python -m pytest app/tests -q; \
		cd ../..; \
	done

frontend-test:  ## Lint + build-check the frontend
	cd frontend && npm run lint && npm run build

build:         ## Build all Docker images
	docker compose build
