data "google_project" "this" {}

locals {
  name = "webcdi-${var.environment}"

  # Environment shared by the web service and the jobs. Secrets are injected
  # separately from Secret Manager.
  env = {
    ALLOWED_HOSTS              = var.allowed_hosts
    ADMINS                     = var.admins
    HTTPS_ONLY                 = "true"
    DB_CONN_MAX_AGE            = "60"
    RDS_DB_NAME                = google_sql_database.app.name
    RDS_USERNAME               = google_sql_user.app.name
    RDS_HOSTNAME               = "/cloudsql/${google_sql_database_instance.db.connection_name}"
    RDS_PORT                   = "5432"
    SITE_ID                    = "1"
    EMAIL_BACKEND              = var.email_backend
    DEFAULT_FROM_EMAIL_NAME    = "Web-CDI"
    DEFAULT_FROM_EMAIL_ADDRESS = "noreply@webcdi.org"
    DEFAULT_RECIPIENT_EMAIL    = "webcdi-contact@stanford.edu"
    SERVER_EMAIL               = "noreply@webcdi.org"
    BROOKES_EMAIL              = var.enable_email_jobs ? "AWagner@brookespublishing.com" : "webcdi-contact@stanford.edu"
    DJANGO_SERVER_TYPE         = upper(var.environment)
  }

  secrets = {
    SECRET_KEY   = google_secret_manager_secret.django_secret_key.secret_id
    RDS_PASSWORD = google_secret_manager_secret.db_password.secret_id
  }

  # Cloud Run jobs: name -> manage.py arguments
  jobs = {
    migrate          = ["migrate", "--noinput"]
    load-instruments = ["load_instruments"]
    scoring          = ["crontab_scoring"]
    monthly-report   = ["monthly_report"]
    weekly-reminder  = ["weekly_reminder"]
  }

  schedules = merge(
    { scoring = "*/10 * * * *" },
    var.enable_email_jobs ? {
      monthly-report  = "0 1 1 * *"
      weekly-reminder = "0 0 * * 0"
    } : {}
  )
}

# --- APIs -------------------------------------------------------------------

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# --- Images -----------------------------------------------------------------

resource "google_artifact_registry_repository" "images" {
  repository_id = "webcdi"
  format        = "DOCKER"
  location      = var.region
  description   = "Web-CDI container images"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 20
    }
  }
  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "2592000s" # 30 days (recent 20 are kept regardless)
    }
  }

  depends_on = [google_project_service.apis]
}

# --- Identity ---------------------------------------------------------------

# Runtime identity for the web service and jobs
resource "google_service_account" "runtime" {
  account_id   = "${local.name}-run"
  display_name = "Web-CDI ${var.environment} runtime"
}

resource "google_project_iam_member" "runtime_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Cloud Scheduler's identity for starting jobs
resource "google_service_account" "scheduler" {
  account_id   = "${local.name}-sched"
  display_name = "Web-CDI ${var.environment} scheduler"
}

# --- Database ---------------------------------------------------------------

resource "google_sql_database_instance" "db" {
  name             = "${local.name}-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 14
      }
    }

    ip_configuration {
      # Public IP with no authorized networks: only reachable through the
      # IAM-authenticated Cloud SQL connector (Cloud Run, cloud-sql-proxy).
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"
    }

    maintenance_window {
      day  = 7  # Sunday
      hour = 10 # UTC
    }

    insights_config {
      query_insights_enabled = true
    }
  }

  deletion_protection = true
  depends_on          = [google_project_service.apis]
}

resource "google_sql_database" "app" {
  name     = "webcdi"
  instance = google_sql_database_instance.db.name
}

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "google_sql_user" "app" {
  name     = "webcdi"
  instance = google_sql_database_instance.db.name
  password = random_password.db.result
}

# --- Secrets ----------------------------------------------------------------
# Generated values are stored in Secret Manager (and, unavoidably, in the
# private tofu state bucket). Externally issued secrets (e.g. the Postmark
# token, #680) are created by hand and only referenced here.

resource "random_password" "django_secret_key" {
  length = 64
}

resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "${local.name}-django-secret-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = random_password.django_secret_key.result
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${local.name}-db-password"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db.result
}

# Project-level grant limited by condition to this environment's secrets
# (resource-level setIamPolicy needs more than Editor + projectIamAdmin).
resource "google_project_iam_member" "runtime_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.runtime.email}"
  condition {
    title      = "${local.name} secrets only"
    expression = "resource.name.startsWith(\"projects/${data.google_project.this.number}/secrets/${local.name}-\")"
  }
}

# --- Web service ------------------------------------------------------------

resource "google_cloud_run_v2_service" "web" {
  name     = local.name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  # Public site. Disabling the invoker check avoids a resource-level allUsers
  # binding (which needs setIamPolicy).
  invoker_iam_disabled = true

  template {
    service_account = google_service_account.runtime.email
    timeout         = "300s"

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.db.connection_name]
      }
    }

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true
      }

      dynamic "env" {
        for_each = local.env
        content {
          name  = env.key
          value = env.value
        }
      }
      dynamic "env" {
        for_each = local.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      startup_probe {
        http_get {
          path = "/health/"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 24
      }
      liveness_probe {
        http_get {
          path = "/health/"
        }
        period_seconds = 30
      }
    }
  }

  # CI/CD deploys new images; don't let `tofu apply` roll them back.
  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }

  depends_on = [
    google_project_iam_member.runtime_secrets,
    google_project_iam_member.runtime_sql,
  ]
}


# --- Jobs (migrations, data loading, scheduled work) ------------------------

resource "google_cloud_run_v2_job" "manage" {
  for_each = local.jobs
  name     = "${local.name}-${each.key}"
  location = var.region

  template {
    task_count = 1
    template {
      service_account = google_service_account.runtime.email
      timeout         = "3600s"
      max_retries     = 0

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.db.connection_name]
        }
      }

      containers {
        image   = var.image
        command = ["python", "manage.py"]
        args    = each.value

        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi"
          }
        }

        dynamic "env" {
          for_each = local.env
          content {
            name  = env.key
            value = env.value
          }
        }
        dynamic "env" {
          for_each = local.secrets
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }

  depends_on = [
    google_project_iam_member.runtime_secrets,
    google_project_iam_member.runtime_sql,
  ]
}

resource "google_project_iam_member" "scheduler_run_jobs" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
  condition {
    title      = "${local.name} jobs only"
    expression = "resource.name.startsWith(\"projects/${var.project_id}/locations/${var.region}/jobs/${local.name}-\")"
  }
}

resource "google_cloud_scheduler_job" "manage" {
  for_each  = local.schedules
  name      = "${local.name}-${each.key}"
  region    = var.region
  schedule  = each.value
  time_zone = "Etc/UTC"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.manage[each.key].name}:run"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  retry_config {
    retry_count = 0
  }

  depends_on = [google_project_iam_member.scheduler_run_jobs]
}
