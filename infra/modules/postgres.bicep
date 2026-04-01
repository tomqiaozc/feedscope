@description('PostgreSQL server name')
param name string

@description('Administrator login name')
param adminUser string = 'feedscopeadmin'

@secure()
@description('Administrator login password')
param adminPassword string

@description('SKU name (e.g. Standard_B1ms)')
param skuName string = 'Standard_B1ms'

@description('SKU tier')
param skuTier string = 'Burstable'

@description('PostgreSQL version')
param version string = '16'

@description('Database name to create')
param databaseName string = 'feedscope'

@description('Azure region')
param location string = resourceGroup().location

@description('Allow Azure services to access this server')
param allowAzureAccess bool = true

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: name
  location: location
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    version: version
    administratorLogin: adminUser
    administratorLoginPassword: adminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgres
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource allowAzureServicesFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = if (allowAzureAccess) {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

@description('PostgreSQL server FQDN')
output fqdn string = postgres.properties.fullyQualifiedDomainName

@description('Full connection string')
output connectionString string = 'postgresql://${adminUser}:${adminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${databaseName}?sslmode=require'

@description('Server resource ID')
output id string = postgres.id
