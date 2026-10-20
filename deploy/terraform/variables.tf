variable "project_id" {
  description = "GCP project (hs-langcog-webcdi; see #690)"
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
  description = "Django email backend (Postmark via anymail; console backend logs mail instead)"
  type        = string
  default     = "anymail.backends.postmark.EmailBackend"
}

variable "postmark_secret_id" {
  description = "Secret Manager secret holding the Postmark server token (created by hand, #680)"
  type        = string
  default     = "postmark-server-token"
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

variable "public" {
  description = "Serve the site publicly. Set false while staging holds a copy of real data (#687); then only private_invokers can reach it (via `gcloud run services proxy`)."
  type        = bool
  default     = true
}

variable "iap_members" {
  description = "Google accounts (\"user:...\") allowed to open a non-public service in the browser via Identity-Aware Proxy, e.g. QA testers during the rehearsal (#687). Personal addresses stay out of the repo: pass them in a gitignored *.local.tfvars."
  type        = list(string)
  default     = []
}

variable "private_invokers" {
  description = "Principals allowed to reach a non-public service"
  type        = list(string)
  default     = ["user:mcfrank@stanford.edu"]
}

variable "log_retention_days" {
  description = "Retention for the project's _Default log bucket (#682)"
  type        = number
  default     = 90
}
