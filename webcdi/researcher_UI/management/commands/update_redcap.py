import logging

from django.core.management.base import BaseCommand

from cdi_forms.scores import update_summary_scores
from researcher_UI.models import Administration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crontab job to update RedCap system"

    def handle(self, *args, **options):
        administrations = Administration.objects.filter(completed=True, send_completion_flag_url_response__isnull=False)

        for instance in administrations:
            instance.save()