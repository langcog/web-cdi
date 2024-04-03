# This file contains settings changed for MPI instance
import json
import os
import socket

import boto3
from botocore.exceptions import ClientError

# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/


def get_secret(secret_name, region_name="us-west-2"):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response["SecretString"]

    return json.loads(secret)


HOST_NAME = socket.gethostname()
HOST_IP = socket.gethostbyname(HOST_NAME)

ALLOWED_HOSTS = [
    "ec2-52-88-52-34.us-west-2.compute.amazonaws.com",
    HOST_IP,
    HOST_NAME,
    "web",  # For tests in using docker
    "test",  # For tests in using docker
    "localhost",
    "127.0.0.2",
    "127.0.0.1",
    ".webcdi.org",
    '.webcdi.stanford.edu',
    '.webcdi-dev.stanford.edu'
]

IPS_TO_ADD = [socket.gethostname()]

NEW_IPS = set()

for IP in IPS_TO_ADD:
    for i in range(0, 100):
        NEW_IPS.add(socket.gethostbyname(IP))

for IP in list(NEW_IPS):
    ALLOWED_HOSTS.append(IP)

ADMINS = (("Henry Mehta", "hjsmehta@gmail.com"),)

DJANGO_SERVER_TYPE = os.environ.get("DJANGO_SERVER_TYPE", "DEV")  # DEV or PROD
# print(get_secret(f"{os.environ.get('DJANGO_SERVER_TYPE','dev').lower()}/webcdi/RDS_PASSWORD")['password'])
# Database Settings
if os.environ.get("DJANGO_SERVER_TYPE", "dev") in ["LOCAL", "TEST"]:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["RDS_DB_NAME"],
            "USER": os.environ["RDS_USERNAME"],
            "PASSWORD": os.environ["RDS_PASSWORD"],
            "HOST": os.environ["RDS_HOSTNAME"],
            "PORT": os.environ["RDS_PORT"],
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "webcdi_postgresql_engine",
            "NAME": os.environ["RDS_DB_NAME"],
            "USER": os.environ["RDS_USERNAME"],
            "PASSWORD": get_secret(
                f"{os.environ.get('DJANGO_SERVER_TYPE','dev').lower()}/webcdi/RDS_PASSWORD"
            )["password"],
            "HOST": os.environ["RDS_HOSTNAME"],
            "PORT": os.environ["RDS_PORT"],
        }
    }

SITE_ID = int(os.environ.get("SITE_ID", 3))  # 4 for MPI, 2 for DEV, 3 for local

# USER_ADMIN_EMAIL = 'webcdi-contact@stanford.edu'
USER_ADMIN_EMAIL = "hjsmehta@gmail.com"

SERVER_EMAIL = "webcdi-contact@stanford.edu"

# captcha settings
RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY", "<RECAPTCHA_PUBLIC_KEY>")
RECAPTCHA_PRIVATE_KEY = os.environ.get(
    "RECAPTCHA_PRIVATE_KEY", "<RECAPTCHA_PRIVATE_KEY>"
)
# Home page links
CONTACT_EMAIL = "webcdi-contact@stanford.edu"
MORE_INFO_ADDRESS = "http://mb-cdi.stanford.edu/"

# AWS creds
secret = get_secret("webcdi/webcdi-IAM")
AWS_ACCESS_KEY_ID = secret["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = secret["AWS_SECRET_ACCESS_KEY"]
if "RDS_HOSTNAME" in os.environ:
    AWS_STORAGE_BUCKET_NAME = os.environ.get(
        "AWS_STORAGE_BUCKET_NAME", "AWS_STORAGE_BUCKET"
    )
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# CAT Server
CAT_API_BASE_URL = os.environ.get(
    "CAT_API_URL", "http://cdicatapi-henry.us-west-2.elasticbeanstalk.com/"
)

# EMAIL settings
AWS_SES_REGION_NAME = "us-west-2"
AWS_SES_REGION_ENDPOINT = "email.us-west-2.amazonaws.com"
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django_ses.SESBackend")
DEFAULT_FROM_EMAIL_NAME = os.environ.get("DEFAULT_FROM_EMAIL_NAME", "WebCDI Local")
DEFAULT_FROM_EMAIL_ADDRESS = os.environ.get(
    "DEFAULT_FROM_EMAIL_ADDRESS", "hjsmehta@gmail.com"
)
DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL_NAME + "<" + DEFAULT_FROM_EMAIL_ADDRESS + ">"
DEFAULT_RECIPIENT_EMAIL = EMAIL_HOST_USER = os.environ.get(
    "DEFAULT_RECIPIENT_EMAIL", "hjsmehta@gmail.com"
)

BROOKES_EMAIL = os.environ.get("BROOKES_EMAIL", "hjsmehta@gmail.com")

PRIMARY_HOST = os.environ.get("PRIMARY_HOST", None)
