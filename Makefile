PY?=python3
PELICAN?=pelican
PORT?=8000
PELICANOPTS=

BASEDIR=$(CURDIR)
INPUTDIR=$(BASEDIR)/content
OUTPUTDIR=$(BASEDIR)/output
CONFFILE=$(BASEDIR)/pelicanconf.py
PUBLISHCONF=$(BASEDIR)/publishconf.py

SSH_HOST=vps
SSH_USER=karelian
SSH_TARGET_DIR=/pv/kube/services/getbetter-www

RSYNC_OPTS?=

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	PELICANOPTS += -D
endif

RELATIVE ?= 0
ifeq ($(RELATIVE), 1)
	PELICANOPTS += --relative-urls
endif

VERIF_FILE=googleef313a2aa1735a89.html

default: help

help:
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep  \
	| sed -e 's/^\(.*\):[^#]*#\(.*\)/\1 \2/' | tr '#' "\t"
	@echo
	@echo 'Set the DEBUG variable to 1 to enable debugging, e.g. make DEBUG=1 html'
	@echo 'Set the RELATIVE variable to 1 to enable relative urls'

html: ### (re)generate the web site
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

clean: ### remove the generated files
	[ ! -d $(OUTPUTDIR) ] || rm -rf $(OUTPUTDIR)

serve: ### serve site at http://localhost:[PORT=8000] and regenerate on file changes
	$(PELICAN) -lr $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS) -p $(PORT)

publish: ## generate using production settings
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(PUBLISHCONF) $(PELICANOPTS)

output/$(VERIF_FILE):
	cp -f var/$(VERIF_FILE) output/

sync: publish output/$(VERIF_FILE) ### upload the web site via rsync+ssh
	git push
	rsync -P -rvzc --cvs-exclude --delete $(RSYNC_OPTS) $(OUTPUTDIR)/ $(SSH_USER)@$(SSH_HOST):$(SSH_TARGET_DIR)

.PHONY: help html clean serve publish sync
