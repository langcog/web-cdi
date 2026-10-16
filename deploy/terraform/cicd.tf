# GitHub Actions deploys with short-lived credentials from Workload Identity
# Federation: no service-account keys exist anywhere. Only workflows in
# var.github_repository can obtain tokens, and the grants below are scoped to
# this environment where IAM conditions allow.

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  depends_on                = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }
  attribute_condition = "assertion.repository == \"${var.github_repository}\""
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

locals {
  github_principal = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

# push images to this repository only
resource "google_project_iam_member" "github_push" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = local.github_principal
  condition {
    title      = "webcdi image repository only"
    expression = "resource.name.startsWith(\"projects/${var.project_id}/locations/${var.region}/repositories/${google_artifact_registry_repository.images.repository_id}\")"
  }
}

# deploy services/jobs and run jobs (operations and executions have their own
# resource names, so this grant is project-wide)
resource "google_project_iam_member" "github_run" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = local.github_principal
}

# deploy revisions that run as the runtime account — and only that account
# (resource-level grant on the service account; needs serviceAccountAdmin)
resource "google_service_account_iam_member" "github_act_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.github_principal
}
