.PHONY: help build build-router up up-router down logs logs-router shell test test-frame test-route test-loop clean

help:
	@echo "MemoryOS Hybrid Desktop System"
	@echo ""
	@echo "Router Commands:"
	@echo "  make build-router       Build lean memoryos-router image (~150MB)"
	@echo "  make up-router          Start router + db (docker-compose-router.yml)"
	@echo "  make down               Stop all services"
	@echo "  make logs-router        Tail router logs"
	@echo "  make shell-router       Open shell in router container"
	@echo ""
	@echo "API Testing:"
	@echo "  make test-health        Check /health endpoint"
	@echo "  make test-frame         Test /api/frame-delta (gating)"
	@echo "  make test-route         Test /api/route (inference)"
	@echo "  make test-loop          Test /api/acknowledge-card (feedback loop)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean              Remove containers, volumes, cache"

build-router:
	docker build -f Dockerfile-router -t memoryos-router:latest .
	@echo "✓ Built: memoryos-router:latest"
	docker images memoryos-router

up-router:
	docker compose -f docker-compose-router.yml up -d
	@echo "✓ Started: memoryos-router"
	@sleep 3
	docker ps -a --filter "label=app=memoryos"

down:
	docker compose -f docker-compose-router.yml down
	@echo "✓ Stopped all services"

logs-router:
	docker logs -f memoryos-router

shell-router:
	docker exec -it memoryos-router /bin/bash

test-health:
	@echo "Testing /health..."
	curl -s http://localhost:5000/health | jq .
	@echo ""

test-frame:
	@echo "Testing /api/frame-delta..."
	curl -s -X POST http://localhost:5000/api/frame-delta \
	  -H "Content-Type: application/json" \
	  -d '{"session_id":"test","frame_delta":{"brightness":0.02,"contrast":0.01,"composite_delta":0.025},"context_hint":"test"}' | jq .
	@echo ""

test-route:
	@echo "Testing /api/route..."
	curl -s -X POST http://localhost:5000/api/route \
	  -H "Content-Type: application/json" \
	  -d '{"session_id":"test","prompt_text":"Describe this frame","max_tokens":256,"user_id":"test","context_from_memory":false}' | jq .
	@echo ""

test-loop:
	@echo "Testing /api/acknowledge-card (feedback loop)..."
	curl -s -X POST "http://localhost:5000/api/acknowledge-card?user_id=test&card_type=vram_thrashing&action=acknowledge" | jq .
	@echo ""
	@echo "Next routing decision should read vram_thrashing_penalty=1.5"
	@echo "Try: make test-route"
	@echo ""

clean:
	docker compose -f docker-compose-router.yml down -v
	rm -rf memory/ tlb_hot_cache/ checkpoints/ graph/ *.db
	docker system prune -f
	@echo "✓ Cleaned up"

docs:
	@echo "📖 API Documentation: http://localhost:5000/docs"
	@echo "📖 Bridge Protocol: see BRIDGE_PROTOCOL.md"
	@echo "📖 Refactor Checklist: see REFACTOR_CHECKLIST.md"
