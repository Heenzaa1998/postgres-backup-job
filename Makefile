SHELL := /bin/bash
# Makefile for postgres-backup-job K8s operations

# Auto-detect kubectl: use kubectl.exe in WSL, kubectl elsewhere
KUBECTL := $(shell if command -v kubectl.exe >/dev/null 2>&1 && uname -r 2>/dev/null | grep -qi microsoft; then echo kubectl.exe; else echo kubectl; fi)

# Configuration (can override: make k8s-ns NAMESPACE=xxx)
NAMESPACE ?= postgres-backup-job
RELEASE ?= backup
CHART := charts/postgres-backup
SECRET_NAME ?= backup-credentials
IMAGE_TAG ?= 1.0.0

.PHONY: help k8s-ns k8s-secret

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help        - Show this help"
	@echo "  k8s-ns      - Create namespace"
	@echo "  k8s-secret  - Create secret from .env file"

k8s-ns: ## Create namespace (override: NAMESPACE=xxx)
	@$(KUBECTL) create namespace $(NAMESPACE) || true

k8s-secret: ## Create secret from .env file
	@$(KUBECTL) create secret generic $(SECRET_NAME) \
		--from-env-file=.env \
		-n $(NAMESPACE) || true
