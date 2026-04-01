@description('Container App name')
param name string

@description('Container Apps Environment resource ID')
param environmentId string

@description('Container image reference')
param image string

@description('Environment variables for the container')
param envVars array = []

@description('CPU cores (e.g. 0.5)')
param cpu string = '0.5'

@description('Memory (e.g. 1Gi)')
param memory string = '1Gi'

@description('Whether ingress is external (public) or internal')
param ingressExternal bool = true

@description('Target port for the container')
param targetPort int = 3000

@description('Minimum number of replicas')
param minReplicas int = 0

@description('Maximum number of replicas')
param maxReplicas int = 3

@description('Liveness probe path')
param livenessPath string = '/health'

@description('Readiness probe path')
param readinessPath string = '/health/ready'

@description('Azure region')
param location string = resourceGroup().location

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  properties: {
    environmentId: environmentId
    configuration: {
      ingress: {
        external: ingressExternal
        targetPort: targetPort
        transport: 'http'
        allowInsecure: false
      }
      registries: []
    }
    template: {
      containers: [
        {
          name: name
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: envVars
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: livenessPath
                port: targetPort
              }
              initialDelaySeconds: 15
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: readinessPath
                port: targetPort
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

@description('Container App FQDN')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Container App URL')
output url string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Container App resource ID')
output id string = containerApp.id
