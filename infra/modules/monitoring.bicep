@description('Name prefix for monitoring resources')
param namePrefix string

@description('Deployment environment')
param env string

@description('Azure region')
param location string = resourceGroup().location

var logAnalyticsName = 'log-${namePrefix}-${env}'
var appInsightsName = 'appi-${namePrefix}-${env}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

@description('Log Analytics Workspace ID')
output workspaceId string = logAnalytics.id

@description('Application Insights connection string')
output connectionString string = appInsights.properties.ConnectionString

@description('Application Insights instrumentation key')
output instrumentationKey string = appInsights.properties.InstrumentationKey
