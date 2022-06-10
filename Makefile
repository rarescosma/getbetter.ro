.DEFAULT_GOAL:=help

PROJECT=getbetter

BUILD_DEPS=$(shell find content -type f)
BUILD_DIR=www

REGISTRY?=localhost:5000
DOCKER_IMAGE=$(REGISTRY)/getbetter-ro:v2

DOCKERFILE?=Dockerfile
REGISTRY?=registry.sys.svc.k8s.local
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

.PHONY: test
test: ## Run python code tests
	mypy getbetter --ignore-missing-imports
	pylint --rcfile=setup.cfg getbetter

.PHONY: drone-mkdocs
drone-mkdocs:
	docker run --rm -v $(PWD):/drone/src -v /sandbox:/sandbox -w /drone/src \
	  $(REGISTRY)/$(PROJECT):$(BUILDER_VERSION) \
	  make build
