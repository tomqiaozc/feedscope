// ============================================================================
// Feedscope — Azure Infrastructure (Bicep)
// Deploys: Monitoring, PostgreSQL, Key Vault, Container Apps Environment,
//          Frontend Container App, Backend Container App
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Deployment environment name')
param env string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Azure Container Registry name (must be globally unique)')
param acrName string

@secure()
@description('PostgreSQL administrator password')
param postgresAdminPassword string

@description('Backend container image reference (e.g. myacr.azurecr.io/backend:latest)')
param backendImage string

@description('Frontend container image reference (e.g. myacr.azurecr.io/frontend:latest)')
param frontendImage string

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

var namePrefix = 'feedscope'
var backendAppName = 'aca-backend-${env}'
var frontendAppName = 'aca-frontend-${env}'
var postgresName = 'psql-feedscope-${env}'
var keyVaultName = 'kv-feedscope-${env}'
var containerEnvName = 'cae-feedscope-${env}'

// ---------------------------------------------------------------------------
// 1. Monitoring — Log Analytics + Application Insights
// ---------------------------------------------------------------------------

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-${env}'
  params: {
    namePrefix: namePrefix
    env: env
    location: location
  }
}

// ---------------------------------------------------------------------------
// 2. Container Apps Environment
// ---------------------------------------------------------------------------

resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(monitoring.outputs.workspaceId, '2023-09-01').customerId
        sharedKey: listKeys(monitoring.outputs.workspaceId, '2023-09-01').primarySharedKey
      }
    }
  }
}

// ---------------------------------------------------------------------------
// 3. PostgreSQL Flexible Server
// ---------------------------------------------------------------------------

module postgres 'modules/postgres.bicep' = {
  name: 'postgres-${env}'
  params: {
    name: postgresName
    adminPassword: postgresAdminPassword
    location: location
  }
}

// ---------------------------------------------------------------------------
// 4. Key Vault
// ---------------------------------------------------------------------------

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

resource dbPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-admin-password'
  properties: {
    value: postgresAdminPassword
  }
}

// ---------------------------------------------------------------------------
// 5. Backend Container App (internal ingress only)
// ---------------------------------------------------------------------------

module backend 'modules/container-app.bicep' = {
  name: 'backend-${env}'
  params: {
    name: backendAppName
    environmentId: containerAppEnv.id
    image: backendImage
    targetPort: 8000
    ingressExternal: false
    cpu: '0.5'
    memory: '1Gi'
    livenessPath: '/health'
    readinessPath: '/health/ready'
    location: location
    envVars: [
      {
        name: 'DATABASE_URL'
        value: postgres.outputs.connectionString
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: monitoring.outputs.connectionString
      }
      {
        name: 'ENV'
        value: env
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// 6. Frontend Container App (external ingress)
// ---------------------------------------------------------------------------

module frontend 'modules/container-app.bicep' = {
  name: 'frontend-${env}'
  params: {
    name: frontendAppName
    environmentId: containerAppEnv.id
    image: frontendImage
    targetPort: 3000
    ingressExternal: true
    cpu: '0.5'
    memory: '1Gi'
    livenessPath: '/health'
    readinessPath: '/health/ready'
    location: location
    envVars: [
      {
        name: 'BACKEND_URL'
        value: 'http://${backendAppName}'
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: monitoring.outputs.connectionString
      }
      {
        name: 'ENV'
        value: env
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Frontend Container App URL')
output frontendUrl string = frontend.outputs.url

@description('Backend Container App (internal) FQDN')
output backendFqdn string = backend.outputs.fqdn

@description('PostgreSQL server FQDN')
output postgresFqdn string = postgres.outputs.fqdn

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Application Insights connection string')
output appInsightsConnectionString string = monitoring.outputs.connectionString
