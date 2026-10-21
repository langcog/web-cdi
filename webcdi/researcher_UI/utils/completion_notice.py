"""Completion notices: POST a study's completion_data to its
send_completion_flag_url when an administration is completed.

The first attempt is made when the administration becomes completed (see
researcher_UI.signals). Failed attempts are recorded on the administration
and retried by the scheduled scoring job (crontab_scoring) until the
researcher's server answers 200 or MAX_ATTEMPTS have been made.
"""

import datetime
import logging

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from researcher_UI.models import Administration

logger = logging.getLogger("debug")

MAX_ATTEMPTS = 5
RETRY_INTERVAL = datetime.timedelta(minutes=10)
REQUEST_TIMEOUT = 30  # seconds


def completion_payload(administration):
    try:
        background_info = administration.backgroundinfo
        source_id = background_info.source_id or ""
        event_id = background_info.event_id or ""
    except ObjectDoesNotExist:
        source_id = event_id = ""
    data = dict(administration.study.completion_data or {})
    for item in data:
        data[item] = (
            data[item]
            .replace("{{source_id}}", source_id)
            .replace("{{event_id}}", event_id)
        )
    return data


def send_completion_notice(administration):
    """Make one attempt; record the response and schedule the next attempt."""
    url = administration.study.send_completion_flag_url
    if not url:
        return

    attempts = administration.completion_notice_attempts + 1
    try:
        response = requests.post(
            url, data=completion_payload(administration), timeout=REQUEST_TIMEOUT
        )
        status = int(response.status_code)
    except requests.RequestException as e:
        logger.warning(
            f"Completion notice for Administration {administration.id} failed: {e}"
        )
        status = None

    next_attempt = None
    if status != 200:
        if attempts < MAX_ATTEMPTS:
            next_attempt = timezone.now() + attempts * RETRY_INTERVAL
        else:
            logger.error(
                f"Failed to get 200 status code for Administration {administration.id} after {attempts} attempts"
            )

    # update() rather than save(): recording the attempt must not fire the
    # Administration save signals again
    Administration.objects.filter(pk=administration.pk).update(
        send_completion_flag_url_response=status,
        completion_notice_attempts=attempts,
        completion_notice_next_attempt=next_attempt,
    )
    administration.send_completion_flag_url_response = status
    administration.completion_notice_attempts = attempts
    administration.completion_notice_next_attempt = next_attempt


def retry_completion_notices():
    """Retry failed completion notices that are due. Returns the number tried."""
    due = (
        Administration.objects.filter(
            completed=True,
            completion_notice_next_attempt__lte=timezone.now(),
            completion_notice_attempts__lt=MAX_ATTEMPTS,
        )
        .exclude(send_completion_flag_url_response=200)
        .select_related("study", "backgroundinfo")
    )
    count = 0
    for administration in due:
        send_completion_notice(administration)
        count += 1
    return count
