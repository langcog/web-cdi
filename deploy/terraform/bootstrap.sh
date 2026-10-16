#!/bin/bash
# One-time setup of the private, versioned bucket that holds tofu state.
# Usage: deploy/terraform/bootstrap.sh <project-id> [region]
set -euo pipefail
PROJECT=$1
REGION=${2:-us-west1}
BUCKET="${PROJECT}-tfstate"
if ! gcloud storage buckets describe "gs://${BUCKET}" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET}" --project "$PROJECT" \
    --location "$REGION" --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage buckets update "gs://${BUCKET}" --versioning
echo "tofu init -backend-config=bucket=${BUCKET}"
