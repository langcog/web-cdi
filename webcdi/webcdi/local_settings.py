# This file contains settings changed for MPI instance
import os
import socket

HOST_NAME = socket.gethostname()
HOST_IP = socket.gethostbyname(HOST_NAME)

ALLOWED_HOSTS = [
    "ec2-52-88-52-34.us-west-2.compute.amazonaws.com",
    HOST_IP,
    HOST_NAME,
    "localhost",
    "127.0.0.2",
    "127.0.0.1",
    "webcdi-dev.us-west-2.elasticbeanstalk.com",
    ".us-west-2.elasticbeanstalk.com",
    "webcdi.stanford.edu",
    "webcdi-dev.stanford.edu",
    ".elb.amazonaws.com",
]

IPS_TO_ADD = [socket.gethostname()]

NEW_IPS = set()

for IP in IPS_TO_ADD:
    for i in range(0, 100):
        NEW_IPS.add(socket.gethostbyname(IP))

for IP in list(NEW_IPS):
    ALLOWED_HOSTS.append(IP)

ADMINS = (("Henry Mehta", "hjsmehta@gmail.com"),)


# Database Settings
if "RDS_HOSTNAME" in os.environ:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["RDS_DB_NAME"],
            "USER": os.environ["RDS_USERNAME"],
            "PASSWORD": os.environ["RDS_PASSWORD"],
            "HOST": os.environ["RDS_HOSTNAME"],
            "PORT": os.environ["RDS_PORT"],
        }
    }
elif "MPI_INSTANCE" in os.environ:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["MPI_DB_NAME"],
            "USER": os.environ["MPI_USERNAME"],
            "PASSWORD": os.environ["MPI_PASSWORD"],
            "HOST": os.environ["MPI_HOSTNAME"],
            "PORT": os.environ["MPI_PORT"],
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "webcdi-admin",
            "USER": "webcdi-admin",
            "PASSWORD": "bears1stlexicon",
            #'HOST': 'webcdiadmin.canyiscnpddk.us-west-2.rds.amazonaws.com',
            "HOST": "webcdi-local-2.canyiscnpddk.us-west-2.rds.amazonaws.com",
            "PORT": "5432",
        }
    }

if "RDS_HOSTNAME" in os.environ:
    if (
        os.environ["RDS_HOSTNAME"]
        == "webcdiadmin.canyiscnpddk.us-west-2.rds.amazonaws.com"
    ):
        os.environ["DJANGO_SERVER_TYPE"] = "PROD"
        os.environ["VANITY_URL"] = "webcdi.stanford.edu"
        SITE_ID = 1
    elif (
        os.environ["RDS_HOSTNAME"]
        == "webcdi-dev-1-py36.canyiscnpddk.us-west-2.rds.amazonaws.com"
    ):
        os.environ["DJANGO_SERVER_TYPE"] = "DEV"
        SITE_ID = 2
    else:
        os.environ["DJANGO_SERVER_TYPE"] = "DEV"
        SITE_ID = 2
elif "MPI_INSTANCE" in os.environ:
    os.environ["DJANGO_SERVER_TYPE"] = "PROD"
    SITE_ID = 4
else:
    os.environ["DJANGO_SERVER_TYPE"] = "DEV"
    SITE_ID = 3

# USER_ADMIN_EMAIL = 'webcdi-contact@stanford.edu'
USER_ADMIN_EMAIL = "hjsmehta@gmail.com"

SERVER_EMAIL = "webcdi-contact@stanford.edu"

# captcha settings
RECAPTCHA_PUBLIC_KEY = "6LfI0yEUAAAAALj8wAxmoXmWg8B64tvr866bXeYg"
RECAPTCHA_PRIVATE_KEY = "6LfI0yEUAAAAALgfbuvciUNhUCLAgslLOtnsFnx3"

# Home page links
CONTACT_EMAIL = "webcdi-contact@stanford.edu"
MORE_INFO_ADDRESS = "http://mb-cdi.stanford.edu/"

# AWS creds
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "<AWS_ACCESS_KEY>")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "<AWS_SECRET_KEY")
if "RDS_HOSTNAME" in os.environ:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "<AWS_ACCESS_KEY>")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "<AWS_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get(
        "AWS_STORAGE_BUCKET_NAME", "AWS_STORAGE_BUCKET"
    )
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# CAT Server
CAT_API_BASE_URL = os.environ.get(
    "CAT_API_URL", "http://cdicatapi-henry.us-west-2.elasticbeanstalk.com/"
)

# Email settings

# EMAIL settings
AWS_SES_REGION_NAME = "us-west-2"
AWS_SES_REGION_ENDPOINT = "email.us-west-2.amazonaws.com"
EMAIL_BACKEND = "django_ses.SESBackend"
DEFAULT_FROM_EMAIL_NAME = os.environ.get("DEFAULT_FROM_EMAIL_NAME", "WebCDI Local")
DEFAULT_FROM_EMAIL_ADDRESS = os.environ.get(
    "DEFAULT_FROM_EMAIL_ADDRESS", "hjsmehta@gmail.com"
)
DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL_NAME + "<" + DEFAULT_FROM_EMAIL_ADDRESS + ">"
DEFAULT_RECIPIENT_EMAIL = EMAIL_HOST_USER = os.environ.get(
    "DEFAULT_RECIPIENT_EMAIL", "hjsmehta@gmail.com"
)

BROOKES_EMAIL = os.environ.get("BROOKES_EMAIL", "hjsmehta@gmail.com")
