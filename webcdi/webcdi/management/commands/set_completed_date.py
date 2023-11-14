from cdi_forms.scores import update_summary_scores
from django.core.management.base import BaseCommand
from researcher_UI.models import Administration


class Command(BaseCommand):
    help = "Crontab job to update Scores of newly completed administrations"

    def handle(self, *args, **options):
        administrations = Administration.objects.filter(completed=True, completed_date__isnull=True)

        count = 0
        for instance in administrations:
            count += 1
            print(f"Processing item {count} of {len(administrations)}")
            instance.completed_date = instance.last_modified
            instance.save()