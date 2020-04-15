.DEFAULT_GOAL := help
SSH_HOST=vps
SSH_USER=karelian
SSH_TARGET_DIR=/pv/kube/services/getbetter-www
RSYNC_OPTS?=--dry-run

help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

site: content ## Build the site using mkdocs
	# python docs/build/main.py
	mkdocs build

.PHONY: serve
serve: ## Serve the site on http://localhost:8000
	# python docs/build/main.py
	mkdocs serve

.PHONY: clean
clean: ## Cleanup
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	rm -rf site
	rm -rf content/_build

.PHONY: sync
sync: site ## Sync the site to the $(SSH_HOST)
	rsync -P -rvzc --delete $(RSYNC_OPTS) site/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)
