# Custom domains (production, #688): a global HTTPS load balancer in front of
# Cloud Run. The Google-managed certificate is authorized through DNS
# (`_acme-challenge` CNAME records, see the dns_authorizations output), so it
# is issued before the domains' A records move to the load balancer.
# Nothing here exists when var.domains is empty (staging).

locals {
  lb       = length(var.domains) > 0
  lb_count = local.lb ? 1 : 0
}

resource "google_compute_global_address" "lb" {
  count      = local.lb_count
  name       = "${local.name}-ip"
  depends_on = [google_project_service.apis]
}

resource "google_certificate_manager_dns_authorization" "domain" {
  for_each   = toset(var.domains)
  name       = "${local.name}-${replace(each.key, ".", "-")}"
  domain     = each.key
  depends_on = [google_project_service.apis]
}

resource "google_certificate_manager_certificate" "site" {
  count = local.lb_count
  name  = "${local.name}-cert"
  managed {
    domains            = var.domains
    dns_authorizations = [for d in var.domains : google_certificate_manager_dns_authorization.domain[d].id]
  }
}

resource "google_certificate_manager_certificate_map" "site" {
  count      = local.lb_count
  name       = "${local.name}-certs"
  depends_on = [google_project_service.apis]
}

resource "google_certificate_manager_certificate_map_entry" "domain" {
  for_each     = toset(var.domains)
  name         = "${local.name}-${replace(each.key, ".", "-")}"
  map          = google_certificate_manager_certificate_map.site[0].name
  hostname     = each.key
  certificates = [google_certificate_manager_certificate.site[0].id]
}

resource "google_compute_region_network_endpoint_group" "web" {
  count                 = local.lb_count
  name                  = "${local.name}-neg"
  region                = var.region
  network_endpoint_type = "SERVERLESS"
  cloud_run {
    service = google_cloud_run_v2_service.web.name
  }
}

resource "google_compute_backend_service" "web" {
  count                 = local.lb_count
  name                  = "${local.name}-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  backend {
    group = google_compute_region_network_endpoint_group.web[0].id
  }
}

resource "google_compute_url_map" "web" {
  count           = local.lb_count
  name            = "${local.name}-lb"
  default_service = google_compute_backend_service.web[0].id
}

# TLS 1.2 or later
resource "google_compute_ssl_policy" "modern" {
  count           = local.lb_count
  name            = "${local.name}-tls"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
  depends_on      = [google_project_service.apis]
}

resource "google_compute_target_https_proxy" "web" {
  count           = local.lb_count
  name            = "${local.name}-https"
  url_map         = google_compute_url_map.web[0].id
  certificate_map = "//certificatemanager.googleapis.com/${google_certificate_manager_certificate_map.site[0].id}"
  ssl_policy      = google_compute_ssl_policy.modern[0].id
}

resource "google_compute_global_forwarding_rule" "https" {
  count                 = local.lb_count
  name                  = "${local.name}-https"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.lb[0].id
  port_range            = "443"
  target                = google_compute_target_https_proxy.web[0].id
}

# Plain HTTP on the same address only redirects to HTTPS
resource "google_compute_url_map" "redirect" {
  count = local.lb_count
  name  = "${local.name}-http-redirect"
  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
  depends_on = [google_project_service.apis]
}

resource "google_compute_target_http_proxy" "redirect" {
  count   = local.lb_count
  name    = "${local.name}-http"
  url_map = google_compute_url_map.redirect[0].id
}

resource "google_compute_global_forwarding_rule" "http" {
  count                 = local.lb_count
  name                  = "${local.name}-http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.lb[0].id
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect[0].id
}
