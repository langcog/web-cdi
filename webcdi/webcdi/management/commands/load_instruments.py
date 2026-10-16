from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

# Order matters: families -> instruments -> scoring -> benchmarks -> choices -> items
STEPS = [
    "01_populate_instrument_family",
    "02_populate_instrument",
    "03_populate_scoring",
    "04a_delete_benchmark",
    "04_populate_benchmark",
    "05_populate_choices",
    "06_populate_items",
]


class Command(BaseCommand):
    help = (
        "Load instrument definitions, scoring, norms, choices and items from the "
        "repo's data files (static/json/instruments.json and friends). Stops at "
        "the first failing step, unlike the old EB deploy hook (#685). Runs in one "
        "transaction, so a failure (e.g. after benchmarks were deleted) rolls "
        "everything back."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for step in STEPS:
            self.stdout.write(f"== {step}")
            call_command(step)
        self.stdout.write(self.style.SUCCESS("instrument data loaded"))
