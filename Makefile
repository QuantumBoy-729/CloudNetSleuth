.PHONY: demo down test logs

demo:  ## One-command local demo: Grafana on :3000, Prometheus on :9090
	docker compose up -d --build
	@echo "Grafana:    http://localhost:3000  (dashboard: CloudNetSleuth)"
	@echo "Prometheus: http://localhost:9090"
	@echo "RCA API:    http://localhost:8080/docs   Ingestor API: http://localhost:8081/docs"

down:
	docker compose down -v

logs:
	docker compose logs -f log-simulator rca-service

test:
	cd services/rca-service && pytest -q
	cd services/log-ingestor && pytest -q
	cd services/log-simulator && pytest -q
