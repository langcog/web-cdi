# Observability (#682): errors are grouped by Cloud Error Reporting (from the
# JSON logs' stack_trace field); these alerts email var.alert_email.

variable "alert_email" {
  type    = string
  default = "webcdi-contact@stanford.edu"
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Web-CDI alerts (${var.environment})"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
  depends_on = [google_project_service.apis]
}

locals {
  channels = [google_monitoring_notification_channel.email.id]
  host     = trimprefix(google_cloud_run_v2_service.web.uri, "https://")
}

# Site up? /health/ checks the database too.
resource "google_monitoring_uptime_check_config" "health" {
  display_name = "${local.name} /health/"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path         = "/health/"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = local.host
    }
  }
}

resource "google_monitoring_alert_policy" "uptime" {
  display_name = "${local.name}: site down"
  combiner     = "OR"
  conditions {
    display_name = "/health/ failing from multiple regions"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND metric.label.check_id=\"${google_monitoring_uptime_check_config.health.uptime_check_id}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "600s"
      aggregations {
        alignment_period     = "1200s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.host"]
      }
    }
  }
  notification_channels = local.channels
}

# Any ERROR log from the service or its jobs (tracebacks, failed commands).
# At most one email per hour; details live in Error Reporting / Logging.
resource "google_monitoring_alert_policy" "errors" {
  display_name = "${local.name}: errors logged"
  combiner     = "OR"
  conditions {
    display_name = "ERROR-level log entry"
    condition_matched_log {
      filter = <<-EOT
        severity>=ERROR AND (
          (resource.type="cloud_run_revision" AND resource.labels.service_name="${local.name}") OR
          (resource.type="cloud_run_job" AND resource.labels.job_name:"${local.name}-")
        )
      EOT
    }
  }
  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }
    auto_close = "1800s"
  }
  notification_channels = local.channels
}

resource "google_monitoring_alert_policy" "job_failures" {
  display_name = "${local.name}: job failed"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run job execution failed"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/job/completed_execution_count\" AND resource.type=\"cloud_run_job\" AND metric.label.result=\"failed\" AND resource.label.job_name=starts_with(\"${local.name}-\")"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.job_name"]
      }
    }
  }
  notification_channels = local.channels
}

resource "google_monitoring_alert_policy" "server_errors" {
  display_name = "${local.name}: 5xx responses"
  combiner     = "OR"
  conditions {
    display_name = "More than 5 server errors in 10 minutes"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${local.name}\" AND metric.label.response_code_class=\"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "0s"
      aggregations {
        alignment_period     = "600s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  notification_channels = local.channels
}

resource "google_monitoring_alert_policy" "database" {
  display_name = "${local.name}: database pressure"
  combiner     = "OR"
  conditions {
    display_name = "CPU above 80% for 15 minutes"
    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\" AND resource.type=\"cloudsql_database\" AND resource.label.database_id=\"${var.project_id}:${google_sql_database_instance.db.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      duration        = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  conditions {
    display_name = "Disk above 85%"
    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/disk/utilization\" AND resource.type=\"cloudsql_database\" AND resource.label.database_id=\"${var.project_id}:${google_sql_database_instance.db.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.85
      duration        = "600s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  notification_channels = local.channels
}
