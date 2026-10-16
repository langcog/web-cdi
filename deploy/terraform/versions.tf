terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0, < 8.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }

  # State lives in a private, versioned bucket in the same project (created
  # once by bootstrap.sh). Pass the bucket at init:
  #   tofu init -backend-config="bucket=<project>-tfstate"
  backend "gcs" {
    prefix = "webcdi"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
