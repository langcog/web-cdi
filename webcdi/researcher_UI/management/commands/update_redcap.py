import logging

from django.core.management.base import BaseCommand

from researcher_UI.models import Administration
from researcher_UI.utils.completion_notice import send_completion_notice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crontab job to update RedCap system"

    def handle(self, *args, **options):
        administrations = Administration.objects.filter(
            completed=True,
            send_completion_flag_url_response__isnull=True,
            completion_notice_attempts=0,
            study__send_completion_flag_url__isnull=False,
        )

        for instance in administrations:
            send_completion_notice(instance)
