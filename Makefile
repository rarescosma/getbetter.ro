.DEFAULT_GOAL := help

help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

.PHONY: docs
docs: ## Build site using mkdocs
	# python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve site using mkdocs
	# python docs/build/main.py
	mkdocs serve

.PHONY: clean
clean: ## Cleanup
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	rm -rf site
	rm -rf content/_build
	rm -rf content/.changelog.md content/.version.md
