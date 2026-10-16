# Production image for Cloud Run (build from the repo root:
#   docker build -f deploy/Dockerfile .)
# The dev image (./Dockerfile) is separate: it bind-mounts the source and adds
# test dependencies.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# WeasyPrint (PDF reports) needs Pango/HarfBuzz and fonts
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY webcdi/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY webcdi/ /app/

# Collect hashed, compressed static files into the image. Settings need their
# required variables to import; these placeholders exist only for this step.
ENV STATIC_ROOT=/app/staticfiles
RUN SECRET_KEY=build-only AWS_INSTANCE=false DEBUG=false \
    ALLOWED_HOSTS='[]' ADMINS='[]' \
    RDS_DB_NAME=x RDS_USERNAME=x RDS_PASSWORD=x RDS_HOSTNAME=x RDS_PORT=5432 \
    DEFAULT_FROM_EMAIL_NAME=x DEFAULT_FROM_EMAIL_ADDRESS=x@example.com \
    DEFAULT_RECIPIENT_EMAIL=x@example.com BROOKES_EMAIL=x@example.com \
    EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend \
    python manage.py collectstatic --noinput -v 0

RUN useradd --create-home --uid 1000 app && mkdir -p /app/media && chown app /app/media
USER app

ENV PORT=8080 AWS_INSTANCE=false LOG_FORMAT=json
EXPOSE 8080
# Cloud Run sends SIGTERM and allows 10 s; --graceful-timeout keeps within it.
CMD exec gunicorn webcdi.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers ${WEB_CONCURRENCY:-2} --threads ${GUNICORN_THREADS:-4} \
    --timeout ${GUNICORN_TIMEOUT:-300} --graceful-timeout 8 \
    --access-logfile -
