variable "project_id" {
  description = "GCP project (hs-langcog-general for now; see #690)"
  type        = string
}

variable "region" {
  type    = string
  default = "us-west1"
}

variable "environment" {
  description = "Name suffix for resources: staging or production"
  type        = string
  default     = "staging"
}

variable "image" {
  description = "Container image for the app (built from deploy/Dockerfile). CI/CD updates it; this is the initial value."
  type        = string
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-g1-small"
}

variable "allowed_hosts" {
  description = "Django ALLOWED_HOSTS (JSON list)"
  type        = string
  default     = "[\".run.app\"]"
}

variable "admins" {
  description = "Django ADMINS (receive request-error emails)"
  type        = string
  default     = "[(\"WebCDI\",\"webcdi-contact@stanford.edu\")]"
}

variable "email_backend" {
  description = "Console backend logs mail instead of sending (staging until Postmark, #680)"
  type        = string
  default     = "django.core.mail.backends.console.EmailBackend"
}

variable "enable_email_jobs" {
  description = "Schedule the Brookes monthly report and renewal reminders (production only)"
  type        = bool
  default     = false
}

variable "min_instances" {
  description = "Minimum Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  type    = number
  default = 3
}

variable "github_repository" {
  description = "GitHub repo allowed to deploy via Workload Identity Federation"
  type        = string
  default     = "langcog/web-cdi"
}
