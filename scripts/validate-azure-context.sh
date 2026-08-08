#!/usr/bin/env bash
set -euo pipefail

environment_name="${1:-dev}"
profile="config/environments/${environment_name}.yaml"

if [[ ! -f "$profile" ]]; then
  echo "Unknown environment profile: $environment_name" >&2
  exit 2
fi

required=(AZURE_SUBSCRIPTION_ID AZURE_TENANT_ID AZURE_RESOURCE_GROUP)
for variable_name in "${required[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Required variable is not set: $variable_name" >&2
    exit 2
  fi
done

az account show >/dev/null
active_subscription="$(az account show --query id -o tsv)"
if [[ "$active_subscription" != "$AZURE_SUBSCRIPTION_ID" ]]; then
  echo "Active Azure subscription does not match AZURE_SUBSCRIPTION_ID" >&2
  echo "Active: $active_subscription" >&2
  echo "Expected: $AZURE_SUBSCRIPTION_ID" >&2
  exit 2
fi

echo "Azure context is valid for $environment_name"
echo "Profile: $profile"
echo "Subscription: $active_subscription"
echo "Resource group: $AZURE_RESOURCE_GROUP"
