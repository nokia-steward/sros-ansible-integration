.PHONY: help install-dev sanity build install import-galaxy validate validate-syntax validate-ansible \
	lint flake8 pylint yamllint ansible-lint security bandit audit ci test docs docs-serve clean \
	test-setup test-sanity test-integration-sros

# Controller: Python 3.12+, ansible-core 2.20+
PYTHON ?= python3
PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
VERSION := $(shell sed -n 's/^version: *//p' galaxy.yml)
BUILD_DIR := .build
SANITY_ROOT := $(BUILD_DIR)/ansible_collections/nokia/sros
SANITY_ARGS ?=
JUNIT_DIR := tests/output/junit
# Test inputs from .github/test-matrix.yml (SROS_VERSION defaults in tests/topo.clab.yml)
ANSIBLE_VERSION ?= 2.22

PLUGIN_PY := $(wildcard plugins/cliconf/*.py plugins/netconf/*.py plugins/terminal/*.py plugins/modules/*.py)
YAML_LINT := galaxy.yml meta/runtime.yml meta/execution-environment.yml \
	playbooks/*.yml playbooks/examples/inventory.yml tests/playbooks.yml tests/inventory.example.yml

help:
	@echo "SR OS Ansible collection — common tasks"
	@echo ""
	@echo "  make install-dev      Install requirements-dev.txt and collection dependencies"
	@echo "  make ci               validate + lint + security (local CI gate)"
	@echo "  make validate         Python syntax + Ansible playbook syntax"
	@echo "  make lint             flake8 + pylint + yamllint + ansible-lint"
	@echo "  make security         bandit (SAST) + pip-audit (dependency CVEs)"
	@echo "  make sanity           ansible-test sanity (under $(SANITY_ROOT))"
	@echo "  make build            Build the collection artifact"
	@echo "  make import-galaxy    Validate built tarball with galaxy-importer"
	@echo "  make test             The suites that need no lab (test-sanity)"
	@echo ""
	@echo "  Test suites of .github/test-matrix.yml (CI and nokia-steward-validator):"
	@echo "  make test-setup       Install ansible-core \$$ANSIBLE_VERSION and the collections"
	@echo "  make test-sanity      ansible-test sanity, JUnit in $(JUNIT_DIR)"
	@echo "  make test-integration-sros   Containerlab SR OS (\$$SROS_VERSION), JUnit in $(JUNIT_DIR)"
	@echo "  make docs             Generate reference and build MkDocs (site/)"
	@echo "  make docs-serve       Serve docs at http://127.0.0.1:8000"
	@echo "  make clean            Remove build artifacts and reports"

install-dev:
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -r requirements-dev.txt
	ansible-galaxy collection install ansible.netcommon ansible.utils community.general

validate: validate-syntax validate-ansible

validate-syntax:
	@echo "Validating Python syntax..."
	$(PYTHON) -m py_compile $(PLUGIN_PY) tools/generate_docs.py
	@echo "Python syntax OK"

validate-ansible:
	ansible-galaxy collection install . --force
	@if [ -f tests/inventory.yml ]; then \
		INV=tests/inventory.yml; \
	else \
		INV=tests/inventory.example.yml; \
	fi; \
	ansible-playbook --syntax-check -i "$$INV" tests/playbooks/*.yml playbooks/*.yml

lint: flake8 pylint yamllint ansible-lint
	@echo "All linting checks passed"

flake8:
	flake8 $(PLUGIN_PY) tools/generate_docs.py --config=.flake8 --show-source --statistics

pylint:
	pylint $(PLUGIN_PY) --rcfile=.pylintrc.plugins --reports=no --fail-under=10
	pylint tools/generate_docs.py --rcfile=.pylintrc --reports=no --fail-under=10

yamllint:
	yamllint -d '{rules: {line-length: {max: 160}}}' $(YAML_LINT)

ansible-lint:
	ansible-lint -c .ansible-lint playbooks/

security: bandit audit
	@echo "All security checks passed"

bandit:
	@echo "Running Bandit SAST on plugins..."
	bandit -r plugins/ tools/generate_docs.py -ll -f txt
	@echo "Bandit scan OK"

audit:
	@echo "Running pip-audit on controller dependencies..."
	pip-audit -r requirements.txt
	@echo "Dependency audit OK"

ci: validate lint security
	@echo "CI pipeline passed (validate + lint + security)"

sanity:
	mkdir -p $(SANITY_ROOT)
	rsync -a --delete --exclude .git --exclude .github --exclude $(BUILD_DIR) --exclude .venv --exclude site \
		--exclude tests/output --exclude 'tests/clab-*' --exclude tests/license.txt ./ $(SANITY_ROOT)/
	ansible-galaxy collection install -p $(BUILD_DIR) ansible.netcommon ansible.utils
	cd $(SANITY_ROOT) && ansible-test sanity --venv --python $(PYTHON_VERSION) -v $(SANITY_ARGS)

build:
	ansible-galaxy collection build . --force

import-galaxy:
	@ARTIFACT="nokia-sros-$(VERSION).tar.gz"; \
	test -f "$$ARTIFACT" || (echo "Artifact $$ARTIFACT not found; run make build first" >&2; exit 1); \
	tools/import_galaxy.sh "$$ARTIFACT"

install: build
	ansible-galaxy collection install nokia-sros-$(VERSION).tar.gz --force

test: test-sanity

# --- Test suites (nokia-steward pattern; inputs are environment variables) -----

test-setup:
	$(PYTHON) -m pip install --upgrade pip
ifeq ($(ANSIBLE_VERSION),devel)
	$(PYTHON) -m pip install -r requirements.txt https://github.com/ansible/ansible/archive/devel.tar.gz
else
	$(PYTHON) -m pip install -r requirements.txt "ansible-core==$(ANSIBLE_VERSION).*"
endif
	ansible-galaxy collection install ansible.netcommon ansible.utils community.general
	ansible-galaxy collection install . --force

test-sanity:
	rm -rf $(SANITY_ROOT)/tests/output/junit
	@status=0; $(MAKE) sanity SANITY_ARGS=--junit || status=$$?; \
	mkdir -p $(JUNIT_DIR); \
	if [ -d $(SANITY_ROOT)/tests/output/junit ]; then cp -R $(SANITY_ROOT)/tests/output/junit/. $(JUNIT_DIR)/; fi; \
	exit $$status

test-integration-sros:
	tests/run.sh integration --topo topo.clab.yml --suite integration-sros

docs:
	$(PYTHON) tools/generate_docs.py
	mkdocs build --clean

docs-serve:
	$(PYTHON) tools/generate_docs.py
	mkdocs serve

clean:
	rm -rf $(BUILD_DIR) site nokia-sros-*.tar.gz bandit-report.json importer_result.json
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
