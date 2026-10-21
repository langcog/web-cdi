import logging

from django.core.management.base import BaseCommand

from cdi_forms.scores import InstrumentScoring, update_summary_scores
from researcher_UI.models import Administration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crontab job to update Scores of newly completed administrations"

    def handle(self, *args, **options):
        administrations = Administration.objects.filter(completed=True, scored=False)

        count = 0
        scoring = {}  # instrument pk -> InstrumentScoring, loaded once per run
        for instance in administrations.select_related("study__instrument"):
            count += 1
            instrument = instance.study.instrument
            if instrument.pk not in scoring:
                scoring[instrument.pk] = InstrumentScoring(instrument)
            try:
                update_summary_scores(instance, scoring[instrument.pk])
            except Exception:
                # one bad administration must not stop scoring for the rest;
                # it stays unscored and is retried (and logged) next run
                logger.exception(f"Scoring failed for administration {instance.pk}")
