project_id  = "hs-langcog-webcdi-prod"
region      = "us-west1"
environment = "production"
# image is passed on the command line for the first apply; CI/CD deploys after

domains = ["webcdi.org", "www.webcdi.org"]
# .run.app stays for the platform's own health probes; the run.app URL itself
# only accepts traffic from the load balancer
allowed_hosts = "[\"webcdi.org\", \"www.webcdi.org\", \".run.app\"]"

github_environment = "production"

db_tier             = "db-custom-1-3840"
db_maintenance_day  = 2  # Tuesday
db_maintenance_hour = 10 # 2 am Pacific in winter, 3 am in summer

min_instances = 1
max_instances = 5

# Brookes monthly report and renewal reminders: off until the Brookes contact
# is confirmed (#688)
enable_email_jobs = false
