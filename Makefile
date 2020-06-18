.DEFAULT_GOAL:=help

SITE_DEPS=$(shell find content -type f)
SITE_DIR=var/www/site

SSH_HOST=vps
SSH_USER=karelian
SSH_TARGET_DIR=/pv/kube/services/getbetter-ro/$(SITE_DIR)
DOCKER_IMAGE=localhost:5000/getbetter-ro:v0
RSYNC_OPTS?=--dry-run
RSYNC_TARGET?=$(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)


help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

$(SITE_DIR): $(SITE_DEPS) ## Build the site using mkdocs
	mkdocs build

.PHONY: serve
serve: ## Serve the site on http://localhost:8000 via MkDocs
	mkdocs serve

.PHONY: gserve
gserve: ## Serve the site on http://localhost:8000 via gunicorn
	cd var/www && gunicorn --reload server:app
	cd -

.PHONY: clean
clean: ## Cleanup
	rm -rf *.egg-info build dist $(SITE_DIR)

.PHONY: sync
sync: $(SITE_DIR) ## Sync the site to the $(SSH_HOST)
	rsync -P -rvzzc --delete $(RSYNC_OPTS) $(SITE_DIR)/ $(RSYNC_TARGET)

.PHONY: docker
docker: ## Build the server docker image
	docker build . -t $(DOCKER_IMAGE)
