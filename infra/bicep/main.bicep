targetScope = 'resourceGroup'

@description('Deployment environment')
param environment string = 'dev'
@description('Azure region')
param location string = resourceGroup().location
@description('Globally unique storage suffix')
param uniqueSuffix string
@allowed([ 'dev', 'test', 'prod' ])
param profile string = environment
param tenantId string
param secureNetworkEnabled bool = false

var namePrefix = 'mlwf-${environment}-${uniqueSuffix}'
var blobDnsZoneName = 'privatelink.blob.${az.environment().suffixes.storage}'
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: { retentionInDays: profile == 'prod' ? 90 : 30 }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower('mlwf${uniqueSuffix}${environment}')
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    publicNetworkAccess: secureNetworkEnabled ? 'Disabled' : 'Enabled'
  }
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-workload'
  location: location
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv'
  location: location
  properties: {
    tenantId: tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: profile == 'prod'
    publicNetworkAccess: secureNetworkEnabled ? 'Disabled' : 'Enabled'
    sku: { family: 'A', name: 'standard' }
  }
}

resource workloadKeyVaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, keyVault.name, identity.name, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
  }
}

resource workloadStorageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, storage.name, identity.name, storageBlobDataContributorRoleId)
  scope: storage
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = if (secureNetworkEnabled) {
  name: '${namePrefix}-vnet'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.40.0.0/16'] }
    subnets: [
      {
        name: 'private-endpoints'
        properties: { addressPrefix: '10.40.1.0/24', privateEndpointNetworkPolicies: 'Disabled' }
      }
    ]
  }
}

resource blobDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (secureNetworkEnabled) {
  name: blobDnsZoneName
  location: 'global'
}

resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (secureNetworkEnabled) {
  parent: blobDnsZone
  name: '${namePrefix}-blob-link'
  location: 'global'
  properties: { virtualNetwork: { id: vnet.id }, registrationEnabled: false }
}

resource storagePrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = if (secureNetworkEnabled) {
  name: '${namePrefix}-storage-pe'
  location: location
  properties: {
    subnet: { id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'private-endpoints') }
    privateLinkServiceConnections: [
      {
        name: '${namePrefix}-storage-connection'
        properties: { privateLinkServiceId: storage.id, groupIds: ['blob'] }
      }
    ]
  }
}

resource storagePrivateDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = if (secureNetworkEnabled) {
  parent: storagePrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      { name: 'blob', properties: { privateDnsZoneId: blobDnsZone.id } }
    ]
  }
}

output logAnalyticsId string = logAnalytics.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output storageId string = storage.id
output workloadIdentityId string = identity.id
output keyVaultId string = keyVault.id
