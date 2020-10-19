.DEFAULT_GOAL:=help

BUILD_DEPS=$(shell find content -type f)
BUILD_DIR=var/build

SSH_HOST=vps
SSH_USER=karelian
SSH_TARGET_DIR=/pv/kube/services/getbetter-ro/$(BUILD_DIR)
DOCKER_IMAGE=localhost:5000/getbetter-ro:v0
RSYNC_OPTS?=--dry-run
RSYNC_TARGET?=$(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)


help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

build: $(BUILD_DIR)/index.html

$(BUILD_DIR)/index.html: $(BUILD_DEPS) ## Build the site using mkdocs
	mkdocs build

.PHONY: serve
serve: ## Serve the site on http://localhost:8000 via MkDocs
	mkdocs serve

.PHONY: gserve
gserve: ## Serve the site on http://localhost:8000 via gunicorn
	cd var && gunicorn --reload server:app
	cd -

.PHONY: clean
clean: ## Cleanup
	rm -rf build dist $(BUILD_DIR)/*

.PHONY: sync
sync: $(BUILD_DIR)/index.html ## Sync the built site to the $(SSH_HOST)
	rsync -P -rvzzc --delete $(RSYNC_OPTS) $(BUILD_DIR)/ $(RSYNC_TARGET)

.PHONY: docker
docker: ## Build the server docker image
	docker build . -t $(DOCKER_IMAGE)

.PHONY: test
test: ## Run python code tests
	mypy getbetter --ignore-missing-imports
	pylint --rcfile=setup.cfg getbetter
