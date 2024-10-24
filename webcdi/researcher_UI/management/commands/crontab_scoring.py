import logging

from django.core.management.base import BaseCommand

from cdi_forms.scores import update_summary_scores
from researcher_UI.models import Administration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crontab job to update Scores of newly completed administrations"

    def handle(self, *args, **options):
        administrations = Administration.objects.filter(completed=True, scored=False)

        count = 0
        for instance in administrations:
            count += 1
            update_summary_scores(instance)
