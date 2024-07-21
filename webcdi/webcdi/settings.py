# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import urllib

from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from webcdi.utils import get_linux_ec2_private_ip

DEBUG = bool(os.environ.get("DEBUG", False))
# DEBUG=False
TEMPLATE_DEBUG = False

try:
    from .secret_settings import *

    print("Importing Secret Settings")
except Exception:
    # print(f"Importing Local Settings with error {e}")
    from .local_settings import *


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/


def generate_secret_key(fname):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    f = open(fname, "w")
    f.write("SECRET_KEY = '%s'\n" % get_random_string(50, chars))


# SECURITY WARNING: keep the secret key used in production secret!
try:
    from .secret_key import *
except ImportError:
    SETTINGS_DIR = os.path.abspath(os.path.dirname(__file__))
    generate_secret_key(os.path.join(SETTINGS_DIR, "secret_key.py"))
    from .secret_key import *

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

MANAGERS = ADMINS

# Application definition
INSTALLED_APPS = (
    "researcher_UI",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "cdi_forms",
    "api",
    "crispy_forms",
    "bootstrap4",
    "bootstrap3",
    "django_tables2",
    "form_utils",
    "django.contrib.sites",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "localflavor",
    "django_countries",
    "webcdi",
    "ckeditor",
    "ckeditor_uploader",
    "brookes",
    "rangefilter",
)

MIDDLEWARE = [
    "webcdi.middleware.PrimaryHostRedirectMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "webcdi.middleware.LoginRequiredMiddleware",
    "webcdi.middleware.AdminLocaleMiddleware",
]

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

AXES_ENABLED = False

ROOT_URLCONF = "webcdi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "researcher_UI.context_processors.get_site_context",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "webcdi.context_processors.home_page",
                "brookes.context_processors.renewal_codes",
            ],
        },
    },
]

WSGI_APPLICATION = "webcdi.wsgi.application"

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
STATIC_URL = "/static/"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap3"

CRISPY_TEMPLATE_PACK = "bootstrap3"


DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap-responsive.html"

LOG_FILE_PATH = str(os.environ.get("LOG_FILE_PATH", "/tmp/"))
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {pathname} {lineno} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            #'class': 'django.utils.log.AdminEmailHandler'
            "class": "logging.FileHandler",
            "filename": f"{LOG_FILE_PATH}django_error.log",
        },
        "file": {
            "level": "DEBUG",
            #'class': 'logging.StreamHandler',
            "class": "logging.FileHandler",
            "filename": f"{LOG_FILE_PATH}django.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            # "class": "logging.FileHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["mail_admins"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "debug": {
            "level": "DEBUG",
            "handlers": ["file", "console"],
            "propagate": True,
        },
        "tests": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

DATE_INPUT_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",  # '2006-10-25', '10/25/2006', '10/25/06'
    "%d/%m/%Y",
    "%d/%m/%y",
    # '%b %d %Y', '%b %d, %Y',             # 'Oct 25 2006', 'Oct 25, 2006'
    # '%d %b %Y', '%d %b, %Y',             # '25 Oct 2006', '25 Oct, 2006'
    # '%B %d %Y', '%B %d, %Y',             # 'October 25 2006', 'October 25, 2006'
    # '%d %B %Y', '%d %B, %Y',             # '25 October 2006', '25 October, 2006'
)


REGISTRATION_SUPPLEMENT_CLASS = "supplementtut.models.MyRegistrationSupplement"
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = True

AXES_LOGIN_FAILURE_LIMIT = 4
# AXES_LOCKOUT_TEMPLATE
AXES_LOCKOUT_URL = "/lockout/"
# AXES_NEVER_LOCKOUT_WHITELIST
# AXES_IP_WHITELIST

"""
if SITE_ID != 3:
    AXES_NUM_PROXIES = 1
    AXES_BEHIND_REVERSE_PROXY = True
"""
AXES_NUM_PROXIES = 1
AXES_BEHIND_REVERSE_PROXY = True

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
    ("es-ar", ("Argentine Spanish")),
    ("fr-ca", _("French Quebec")),
    ("fr", _("French French")),
    ("en-ca", _("Canadian English")),
    ("nl", _("Dutch")),
    ("he", _("Hebrew")),
    ("ko", _("Korean")),
    ("ja", _("Japanese")),
]

# this is used to find the right choices etc for a language
LANGUAGE_DICT = {
    "English": "en",
    "Spanish": "es",
    "French Quebec": "fr_ca",
    "French French": "fr",
    "Canadian English": "en_ca",
    "Dutch": "nl",
    "Hebrew": "he",
    "Korean": "ko",
    "Argentine Spanish": "es_ar",
    "Japanese": "ja",
}

LANGUAGE_TO_COUNTRY_DICT = {
    "Dutch": "nl",
}


COUNTRIES_FIRST = ["US", "CA", "NL", "IL", "JP", "FR", "CH", "BE", "LU"]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

CKEDITOR_UPLOAD_PATH = "ckeditor_uploads/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": [
            {
                "name": "document",
                "items": [
                    "Source",
                    "-",
                    "Save",
                    "NewPage",
                    "Preview",
                    "Print",
                    "-",
                    "Templates",
                ],
            },
            {
                "name": "clipboard",
                "items": [
                    "Cut",
                    "Copy",
                    "Paste",
                    "PasteText",
                    "PasteFromWord",
                    "-",
                    "Undo",
                    "Redo",
                ],
            },
            {"name": "editing", "items": ["Find", "Replace", "-", "SelectAll"]},
            {
                "name": "forms",
                "items": [
                    "Form",
                    "Checkbox",
                    "Radio",
                    "TextField",
                    "Textarea",
                    "Select",
                    "Button",
                    "ImageButton",
                    "HiddenField",
                ],
            },
            "/",
            {
                "name": "basicstyles",
                "items": [
                    "Bold",
                    "Italic",
                    "Underline",
                    "Strike",
                    "Subscript",
                    "Superscript",
                    "-",
                    "RemoveFormat",
                ],
            },
            {
                "name": "paragraph",
                "items": [
                    "NumberedList",
                    "BulletedList",
                    "-",
                    "Outdent",
                    "Indent",
                    "-",
                    "Blockquote",
                    "CreateDiv",
                    "-",
                    "JustifyLeft",
                    "JustifyCenter",
                    "JustifyRight",
                    "JustifyBlock",
                    "-",
                    "BidiLtr",
                    "BidiRtl",
                    "Language",
                ],
            },
            {"name": "links", "items": ["Link", "Unlink", "Anchor"]},
            {
                "name": "insert",
                "items": [
                    "Image",
                    "Flash",
                    "Table",
                    "HorizontalRule",
                    "Smiley",
                    "SpecialChar",
                    "PageBreak",
                    "Iframe",
                ],
            },
            "/",
            {"name": "styles", "items": ["Styles", "Format", "Font", "FontSize"]},
            {"name": "colors", "items": ["TextColor", "BGColor"]},
            {"name": "tools", "items": ["Maximize", "ShowBlocks"]},
        ],
        #'skin': 'moono',
        #'toolbar': None,
        "height": "100%",
        "width": "100%",
    }
}

AWS_QUERYSTRING_AUTH = False

LOGOUT_REDIRECT_URL = "/"


private_ip = get_linux_ec2_private_ip()
if private_ip:
    ALLOWED_HOSTS.append(private_ip)

CAT_FORMS = ["CAT", "CAT2"]

LOGIN_EXEMPT_URLS = (
    r"^registration/logout/$",
    r"^registration/register/$",
    r"^registration/password-reset/$",
    r"^registration/password-reset/done/$",
    r"^registration/password-reset/confirm/",
    r"^registration/password-reset/complete/$",
    r"^registration/password/change/$",
    r"^registration/password/change/",
    r"^",
)


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
