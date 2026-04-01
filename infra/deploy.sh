#!/usr/bin/env bash
# ============================================================================
# Feedscope — Azure Deployment Script
# Provisions resources in the shared rg-rewind-ea resource group:
#   - feedscope database on existing pg-rwnd-prod PostgreSQL
#   - Application Insights instance
#   - Backend + Frontend Web Apps on existing plan-rwnd-prod
#   - Key Vault secrets in existing kv-rwnd-prod
#
# Prerequisites:
#   - az CLI logged in with sufficient permissions
#   - GHCR_TOKEN (GitHub PAT with packages:read for private images)
# ============================================================================
set -euo pipefail

RG="rg-rewind-ea"
PG_SERVER="pg-rwnd-prod"
PG_DB="feedscope"
PLAN="plan-rwnd-prod"
KV="kv-rwnd-prod"
LOG_WORKSPACE="log-rwnd-prod"
BACKEND_APP="app-backend-feedscope-prod"
FRONTEND_APP="app-frontend-feedscope-prod"
AI_NAME="ai-feedscope-prod"
GHCR_IMAGE_BACKEND="ghcr.io/tomqiaozc/feedscope/backend:latest"
GHCR_IMAGE_FRONTEND="ghcr.io/tomqiaozc/feedscope/frontend:latest"

echo "=== Feedscope Deployment ==="
echo "Resource Group : ${RG}"
echo "PostgreSQL     : ${PG_SERVER}/${PG_DB}"
echo "App Service    : ${PLAN}"
echo ""

# ---------------------------------------------------------------------------
# 1. Create feedscope database on shared PostgreSQL
# ---------------------------------------------------------------------------
echo "--- Creating database '${PG_DB}' on ${PG_SERVER}..."
az postgres flexible-server db create \
  --resource-group "${RG}" \
  --server-name "${PG_SERVER}" \
  --database-name "${PG_DB}" \
  --output none 2>/dev/null || echo "    (database already exists)"

# ---------------------------------------------------------------------------
# 2. Create Application Insights
# ---------------------------------------------------------------------------
echo "--- Creating Application Insights '${AI_NAME}'..."
AI_CONN=$(az monitor app-insights component create \
  --app "${AI_NAME}" \
  --location eastasia \
  --resource-group "${RG}" \
  --workspace "${LOG_WORKSPACE}" \
  --query "connectionString" \
  --output tsv 2>/dev/null) || \
AI_CONN=$(az monitor app-insights component show \
  --app "${AI_NAME}" \
  --resource-group "${RG}" \
  --query "connectionString" \
  --output tsv)
echo "    Connection string obtained."

# ---------------------------------------------------------------------------
# 3. Create Backend Web App
# ---------------------------------------------------------------------------
echo "--- Creating backend Web App '${BACKEND_APP}'..."
az webapp create \
  --name "${BACKEND_APP}" \
  --resource-group "${RG}" \
  --plan "${PLAN}" \
  --deployment-container-image-name "${GHCR_IMAGE_BACKEND}" \
  --output none 2>/dev/null || echo "    (already exists)"

# Get PostgreSQL connection info for DATABASE_URL
PG_FQDN=$(az postgres flexible-server show \
  --name "${PG_SERVER}" \
  --resource-group "${RG}" \
  --query "fullyQualifiedDomainName" \
  --output tsv)

echo "--- Configuring backend environment variables..."
az webapp config appsettings set \
  --name "${BACKEND_APP}" \
  --resource-group "${RG}" \
  --settings \
    WEBSITES_PORT=8000 \
    E2E_SKIP_AUTH=false \
    MOCK_PROVIDER=false \
    APPLICATIONINSIGHTS_CONNECTION_STRING="${AI_CONN}" \
    CORS_ORIGINS="https://${FRONTEND_APP}.azurewebsites.net" \
  --output none

echo "    NOTE: Set DATABASE_URL manually (contains password):"
echo "    az webapp config appsettings set --name ${BACKEND_APP} --resource-group ${RG} \\"
echo "      --settings DATABASE_URL='postgresql+asyncpg://USER:PASS@${PG_FQDN}:5432/${PG_DB}?sslmode=require'"

# ---------------------------------------------------------------------------
# 4. Create Frontend Web App
# ---------------------------------------------------------------------------
echo "--- Creating frontend Web App '${FRONTEND_APP}'..."
az webapp create \
  --name "${FRONTEND_APP}" \
  --resource-group "${RG}" \
  --plan "${PLAN}" \
  --deployment-container-image-name "${GHCR_IMAGE_FRONTEND}" \
  --output none 2>/dev/null || echo "    (already exists)"

echo "--- Configuring frontend environment variables..."
az webapp config appsettings set \
  --name "${FRONTEND_APP}" \
  --resource-group "${RG}" \
  --settings \
    WEBSITES_PORT=3000 \
    BACKEND_URL="https://${BACKEND_APP}.azurewebsites.net" \
    NEXTAUTH_URL="https://${FRONTEND_APP}.azurewebsites.net" \
  --output none

echo "    NOTE: Set secrets manually:"
echo "    az webapp config appsettings set --name ${FRONTEND_APP} --resource-group ${RG} \\"
echo "      --settings NEXTAUTH_SECRET='...' GOOGLE_CLIENT_ID='...' GOOGLE_CLIENT_SECRET='...'"

# ---------------------------------------------------------------------------
# 5. Enable managed identity + Key Vault access (optional)
# ---------------------------------------------------------------------------
echo "--- Enabling system-assigned managed identity..."
az webapp identity assign --name "${BACKEND_APP}" --resource-group "${RG}" --output none
az webapp identity assign --name "${FRONTEND_APP}" --resource-group "${RG}" --output none

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Frontend : https://${FRONTEND_APP}.azurewebsites.net"
echo "Backend  : https://${BACKEND_APP}.azurewebsites.net"
echo "Health   : https://${BACKEND_APP}.azurewebsites.net/health"
echo ""
echo "Next steps:"
echo "  1. Set DATABASE_URL on backend (see command above)"
echo "  2. Set NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET on frontend"
echo "  3. Run Alembic migration: az webapp ssh --name ${BACKEND_APP} -g ${RG}"
echo "     Then: alembic upgrade head"
echo "  4. Update Google OAuth callback URL to:"
echo "     https://${FRONTEND_APP}.azurewebsites.net/api/auth/callback/google"
echo ""
echo "Logs:"
echo "  az webapp log tail --name ${BACKEND_APP} -g ${RG}"
echo "  az webapp log tail --name ${FRONTEND_APP} -g ${RG}"
