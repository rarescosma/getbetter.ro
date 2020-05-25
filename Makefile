.DEFAULT_GOAL:=help
SSH_HOST=vps
SSH_USER=karelian
SSH_TARGET_DIR=/pv/kube/services/getbetter-www
DOCKER_IMAGE=localhost:5000/getbetter-ro:v0
RSYNC_OPTS?=--dry-run

SITE_DEPS=$(shell find content -type f)

help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

site: $(SITE_DEPS) ## Build the site using mkdocs
	mkdocs build

.PHONY: serve
serve: ## Serve the site on http://localhost:8000 via MkDocs
	mkdocs serve

.PHONY: gserve
gserve: ## Serve the site on http://localhost:8000 via gunicorn
	gunicorn --reload server:app

.PHONY: clean
clean: ## Cleanup
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	rm -rf site
	rm -rf content/_build

.PHONY: sync
sync: site ## Sync the site to the $(SSH_HOST)
	rsync -P -rvzzc --delete $(RSYNC_OPTS) site/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)

.PHONY: docker
docker: ## Build the server docker image
	docker build . -t $(DOCKER_IMAGE)
