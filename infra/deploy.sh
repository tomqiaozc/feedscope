#!/usr/bin/env bash
# ============================================================================
# Feedscope — Azure Deployment Script
# Deploys the Bicep infrastructure template with the specified environment.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Configuration (override via environment variables)
# ---------------------------------------------------------------------------
ENV="${ENV:-dev}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-feedscope-${ENV}}"
LOCATION="${LOCATION:-eastus}"
PARAM_FILE="${PARAM_FILE:-${SCRIPT_DIR}/parameters/${ENV}.bicepparam}"

# ---------------------------------------------------------------------------
# Validate prerequisites
# ---------------------------------------------------------------------------
if ! command -v az &>/dev/null; then
  echo "Error: Azure CLI (az) is not installed." >&2
  exit 1
fi

if [ -z "${POSTGRES_ADMIN_PASSWORD:-}" ]; then
  echo "Error: POSTGRES_ADMIN_PASSWORD environment variable is required." >&2
  exit 1
fi

echo "=== Feedscope Deployment ==="
echo "Environment : ${ENV}"
echo "Resource Group: ${RESOURCE_GROUP}"
echo "Location : ${LOCATION}"
echo "Parameter File: ${PARAM_FILE}"
echo ""

# ---------------------------------------------------------------------------
# 1. Create resource group if it doesn't exist
# ---------------------------------------------------------------------------
echo "--- Ensuring resource group '${RESOURCE_GROUP}' exists..."
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --output none

# ---------------------------------------------------------------------------
# 2. Deploy Bicep template
# ---------------------------------------------------------------------------
echo "--- Deploying Bicep template..."
DEPLOYMENT_OUTPUT=$(az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${SCRIPT_DIR}/main.bicep" \
  --parameters "${PARAM_FILE}" \
  --parameters postgresAdminPassword="${POSTGRES_ADMIN_PASSWORD}" \
  --name "feedscope-${ENV}-$(date +%Y%m%d%H%M%S)" \
  --output json)

# ---------------------------------------------------------------------------
# 3. Print deployment outputs
# ---------------------------------------------------------------------------
echo ""
echo "=== Deployment Complete ==="
echo ""

FRONTEND_URL=$(echo "${DEPLOYMENT_OUTPUT}" | jq -r '.properties.outputs.frontendUrl.value // "N/A"')
BACKEND_FQDN=$(echo "${DEPLOYMENT_OUTPUT}" | jq -r '.properties.outputs.backendFqdn.value // "N/A"')
POSTGRES_FQDN=$(echo "${DEPLOYMENT_OUTPUT}" | jq -r '.properties.outputs.postgresFqdn.value // "N/A"')
KEYVAULT_NAME=$(echo "${DEPLOYMENT_OUTPUT}" | jq -r '.properties.outputs.keyVaultName.value // "N/A"')

echo "Frontend URL : ${FRONTEND_URL}"
echo "Backend FQDN (internal): ${BACKEND_FQDN}"
echo "PostgreSQL FQDN : ${POSTGRES_FQDN}"
echo "Key Vault : ${KEYVAULT_NAME}"
echo ""
echo "To stream frontend logs:"
echo "  az containerapp logs show -n aca-frontend-${ENV} -g ${RESOURCE_GROUP} --follow"
echo ""
echo "To stream backend logs:"
echo "  az containerapp logs show -n aca-backend-${ENV} -g ${RESOURCE_GROUP} --follow"
