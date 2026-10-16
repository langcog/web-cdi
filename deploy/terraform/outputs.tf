output "service_url" {
  value = google_cloud_run_v2_service.web.uri
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "db_connection_name" {
  value = google_sql_database_instance.db.connection_name
}

output "runtime_service_account" {
  value = google_service_account.runtime.email
}

output "jobs" {
  value = [for j in google_cloud_run_v2_job.manage : j.name]
}

output "github_wif_provider" {
  description = "Set as the GCP_WIF_PROVIDER repository variable"
  value       = google_iam_workload_identity_pool_provider.github.name
}
