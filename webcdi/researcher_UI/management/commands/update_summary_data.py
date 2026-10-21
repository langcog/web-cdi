import datetime
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from cdi_forms.scores import InstrumentScoring, update_summary_scores
from researcher_UI.models import Administration, Study

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-s", "--study_id", type=int)
        parser.add_argument("-l", "--language", type=str)
        parser.add_argument("-f", "--form", type=str)
        parser.add_argument("-u", "--username", type=str)

    def handle(self, *args, **options):
        query = Q()
        if options["study_id"]:
            study_obj = Study.objects.get(pk=options["study_id"])
            query = Q(study=study_obj)
        if options["language"]:
            query = Q(query) & Q(study__instrument__language=options["language"])
        if options["form"]:
            query = Q(query) & Q(study__instrument__form=options["form"])
        if options["username"]:
            query = Q(query) & Q(study__researcher__username=options["username"])

        administrations = Administration.objects.filter(query).filter(completed=True)

        total = administrations.count()
        count = 0
        failed = []
        scoring = {}  # instrument pk -> InstrumentScoring, loaded once per run
        for instance in administrations.select_related("study__instrument"):
            count += 1
            instrument = instance.study.instrument
            if instrument.pk not in scoring:
                scoring[instrument.pk] = InstrumentScoring(instrument)
            try:
                update_summary_scores(instance, scoring[instrument.pk])
            except Exception:
                # keep going: one bad administration must not stop a full rescore
                logger.exception(f"Scoring failed for administration {instance.pk}")
                failed.append(instance.pk)
            if count % 1000 == 0:
                self.stdout.write(f"{count} of {total} rescored")

        # progress goes to the job log (Cloud Run); failures alert via monitoring
        self.stdout.write(f"COMPLETED at {datetime.datetime.now()}: {count} rescored")
        if failed:
            raise CommandError(
                f"{len(failed)} administrations failed to score (see log): {failed[:50]}"
            )
