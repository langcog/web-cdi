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

output "lb_ip" {
  description = "Load balancer address: the A record for each domain at cutover"
  value       = local.lb ? google_compute_global_address.lb[0].address : null
}

output "dns_authorizations" {
  description = "CNAME records to add before cutover so the certificate can be issued"
  value       = { for d, a in google_certificate_manager_dns_authorization.domain : d => a.dns_resource_record[0] }
}
