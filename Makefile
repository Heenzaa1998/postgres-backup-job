SHELL := /bin/bash
# Makefile for postgres-backup-job K8s operations

# Auto-detect kubectl: use kubectl.exe in WSL, kubectl elsewhere
KUBECTL := $(shell if command -v kubectl.exe >/dev/null 2>&1 && uname -r 2>/dev/null | grep -qi microsoft; then echo kubectl.exe; else echo kubectl; fi)

# Auto-detect helm: use helm.exe in WSL, helm elsewhere
HELM := $(shell if command -v helm.exe >/dev/null 2>&1 && uname -r 2>/dev/null | grep -qi microsoft; then echo helm.exe; else echo helm; fi)


# Configuration (can override: make k8s-ns NAMESPACE=xxx)
NAMESPACE ?= postgres-backup-job
RELEASE ?= backup
CHART := charts/postgres-backup
SECRET_NAME ?= backup-credentials
IMAGE_TAG ?= 1.0.0

.PHONY: help k8s-ns k8s-secret k8s-deploy k8s-test k8s-logs k8s-pvc k8s-status k8s-download k8s-clean

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help         - Show this help"
	@echo "  k8s-ns       - Create namespace"
	@echo "  k8s-secret   - Create secret from .env file"
	@echo "  k8s-deploy   - Deploy helm chart"
	@echo "  k8s-test     - Trigger backup job and show logs"
	@echo "  k8s-logs     - View latest backup logs"
	@echo "  k8s-pvc      - List backup files in PVC"
	@echo "  k8s-status   - Show all resources status"
	@echo "  k8s-download - Download backups from PVC to ./backups"
	@echo "  k8s-clean    - Delete all resources"

k8s-ns: ## Create namespace (override: NAMESPACE=xxx)
	@$(KUBECTL) create namespace $(NAMESPACE) || true

k8s-secret: ## Create secret from .env file
	@$(KUBECTL) create secret generic $(SECRET_NAME) \
		--from-env-file=.env \
		-n $(NAMESPACE) || true

k8s-deploy: k8s-ns k8s-secret ## Deploy helm chart
	@$(HELM) install $(RELEASE) $(CHART) \
		-n $(NAMESPACE) \
		--set secret.existingSecretName=$(SECRET_NAME) \
		--set image.tag=$(IMAGE_TAG)

k8s-test: ## Trigger manual backup job and show logs
	@$(KUBECTL) delete job manual-backup -n $(NAMESPACE) 2>/dev/null || true
	@$(KUBECTL) create job --from=cronjob/$(RELEASE)-postgres-backup manual-backup \
		-n $(NAMESPACE)
	@echo "Waiting for pod to start..."
	@$(KUBECTL) wait --for=condition=Ready pod -l job-name=manual-backup -n $(NAMESPACE) --timeout=60s 2>/dev/null || true
	@$(KUBECTL) logs -l job-name=manual-backup -n $(NAMESPACE) -f

k8s-logs: ## View latest backup logs
	@$(KUBECTL) logs -l app.kubernetes.io/name=postgres-backup -n $(NAMESPACE) --tail=100

k8s-pvc: ## List backup files in PVC
	@$(KUBECTL) run pvc-viewer --image=busybox -n $(NAMESPACE) --rm -it --restart=Never \
		--overrides='{"spec":{"containers":[{"name":"pvc-viewer","image":"busybox","command":["ls","-la","/backups"],"volumeMounts":[{"name":"backup","mountPath":"/backups"}]}],"volumes":[{"name":"backup","persistentVolumeClaim":{"claimName":"$(RELEASE)-postgres-backup"}}]}}' \
		2>/dev/null || echo "PVC may not exist or no backups yet"

k8s-status: ## Show all resources status
	@echo "=== Namespace: $(NAMESPACE) ==="
	@$(KUBECTL) get cronjob,job,pod,pvc,secret -n $(NAMESPACE)

k8s-download: ## Download backups from PVC to ./backups
	@echo "Starting download pod..."
	@$(KUBECTL) run pvc-download --image=busybox -n $(NAMESPACE) --restart=Never \
		--overrides='{"spec":{"containers":[{"name":"pvc-download","image":"busybox","command":["sleep","300"],"volumeMounts":[{"name":"backup","mountPath":"/backups"}]}],"volumes":[{"name":"backup","persistentVolumeClaim":{"claimName":"$(RELEASE)-postgres-backup"}}]}}' \
		2>/dev/null || true
	@$(KUBECTL) wait --for=condition=Ready pod/pvc-download -n $(NAMESPACE) --timeout=60s
	@echo "Copying files..."
	@$(KUBECTL) cp $(NAMESPACE)/pvc-download:/backups ./backups
	@$(KUBECTL) delete pod pvc-download -n $(NAMESPACE)
	@echo "Downloaded to ./backups"

k8s-clean: ## Delete all resources
	@echo "Cleaning up..."
	@$(HELM) uninstall $(RELEASE) -n $(NAMESPACE) 2>/dev/null || true
	@$(KUBECTL) delete pvc $(RELEASE)-postgres-backup -n $(NAMESPACE) 2>/dev/null || true
	@$(KUBECTL) delete secret $(SECRET_NAME) -n $(NAMESPACE) 2>/dev/null || true
	@$(KUBECTL) delete namespace $(NAMESPACE) 2>/dev/null || true
	@echo "Cleanup complete"
