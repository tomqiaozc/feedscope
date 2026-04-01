using '../main.bicep'

param env = 'dev'
param acrName = 'acrfeedscope'
param postgresAdminPassword = readEnvironmentVariable('POSTGRES_ADMIN_PASSWORD', '')
param backendImage = 'acrfeedscope.azurecr.io/backend:latest'
param frontendImage = 'acrfeedscope.azurecr.io/frontend:latest'
