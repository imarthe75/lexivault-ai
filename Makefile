SHELL := /bin/bash
.PHONY: redeploy redeploy-force prune

# Redeploy locally (interactive prune)
redeploy:
	./scripts/redeploy.sh

# Redeploy and force prune (non-interactive)
redeploy-force:
	AUTO_PRUNE=1 ./scripts/redeploy.sh

# Direct prune helpers (local)
prune:
	docker system prune -a --volumes -f
	docker builder prune -a -f
