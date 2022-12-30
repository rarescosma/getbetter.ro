.DEFAULT_GOAL:=help

PROJECT=getbetter.ro

BUILD_DEPS=$(shell find content -type f)
BUILD_DIR=www
LIVE_DIR=var/www

REGISTRY?=registry-np.storage-system.svc.k8s.local:5000

DOCKERFILE?=Dockerfile
BUILDER_VERSION?=$(shell ./docker/hacks/builder-version.sh)
PROJECT_VERSION?=$(shell ./docker/hacks/project-version.sh)
PROJECT_TAG=$(PROJECT):$(PROJECT_VERSION)

BUILDER_MAKE=$(MAKE) PROJECT_VERSION=$(BUILDER_VERSION)

help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

build: $(BUILD_DIR)/index.html ## Build the site using mkdocs

$(BUILD_DIR)/index.html: $(BUILD_DEPS)
	mkdocs build

.PHONY: serve
serve: ## Serve the site on http://localhost:8000 via MkDocs
	mkdocs serve

.PHONY: gserve
gserve: ## Serve the site on http://localhost:8000 via gunicorn
	gunicorn --reload getbetter.server:app

.PHONY: clean
clean: ## Cleanup
	rm -rf build dist $(BUILD_DIR)/*

.PHONY: sync
sync: build ## Sync the live website to $(LIVE_DIR)
	rsync -avP --delete --checksum $(BUILD_DIR)/ $(LIVE_DIR)/

.PHONY: builder
builder: ## Build the builder
	@$(BUILDER_MAKE) pull || ( \
      DOCKERFILE='Dockerfile-builder' $(BUILDER_MAKE) docker \
      && $(BUILDER_MAKE) push \
    )

.PHONY: pull
pull: ## Pull docker image
	docker pull $(REGISTRY)/$(PROJECT_TAG)

.PHONY: docker
docker: ## Build the docker image
	docker build -t $(REGISTRY)/$(PROJECT_TAG) \
	  --build-arg BUILDER_VERSION=$(BUILDER_VERSION) \
	  --build-arg REGISTRY=$(REGISTRY) \
	  -f docker/$(DOCKERFILE) .

.PHONY: push
push:  ## Publish the docker image
	docker push $(REGISTRY)/$(PROJECT_TAG)

.PHONY: push-head
push-head:
	docker tag $(REGISTRY)/$(PROJECT_TAG) $(REGISTRY)/$(PROJECT):v2.1
	docker push $(REGISTRY)/$(PROJECT):v2.1

.PHONY: test
test: ## Run python code tests
	mypy getbetter --ignore-missing-imports
	pylint --rcfile=setup.cfg getbetter

.PHONY: drone-mkdocs
drone-mkdocs:
	docker run --rm -v $(PWD):/drone/src -v /sandbox:/sandbox -w /drone/src \
	  $(REGISTRY)/$(PROJECT):$(BUILDER_VERSION) \
	  make build
