"""Check that the bulk scorer matches the legacy row-by-row scorer (#668).

Scores each selected administration with both implementations inside a
rolled-back transaction and reports any difference in SummaryData rows, the
`scored` flag, or raised errors. Writes nothing. Intended for a copy of
production data (e.g. GCP staging during the migration rehearsal, #687).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from cdi_forms import scores, scores_legacy
from researcher_UI.models import Administration, SummaryData


def _run(score, administration_id):
    admin = Administration.objects.select_related("study__instrument").get(
        pk=administration_id
    )
    with transaction.atomic():
        try:
            score(admin)
            error = None
        except Exception as e:  # compare failures too
            error = type(e).__name__
        rows = dict(
            SummaryData.objects.filter(administration=admin).values_list(
                "title", "value"
            )
        )
        scored = Administration.objects.get(pk=admin.pk).scored
        transaction.set_rollback(True)
    return {"rows": rows, "scored": scored, "error": error}


def compare_administration(administration_id):
    """Return (legacy, new, differences) for one administration."""
    legacy = _run(scores_legacy.update_summary_scores, administration_id)
    new = _run(scores.update_summary_scores, administration_id)
    differences = []
    for key in ("scored", "error"):
        if legacy[key] != new[key]:
            differences.append(f"{key}: legacy={legacy[key]!r} new={new[key]!r}")
    for title in sorted(set(legacy["rows"]) | set(new["rows"])):
        a, b = legacy["rows"].get(title), new["rows"].get(title)
        if a != b:
            differences.append(f"{title!r}: legacy={a!r} new={b!r}")
    return legacy, new, differences


class Command(BaseCommand):
    help = "Compare legacy vs bulk scoring on completed administrations (writes nothing)."

    def add_arguments(self, parser):
        parser.add_argument("--instrument", help="instrument name, e.g. English_WS")
        parser.add_argument("--study", type=int)
        parser.add_argument("--limit", type=int, default=200)

    def handle(self, *args, **options):
        qs = Administration.objects.filter(completed=True).order_by("?")
        if options["instrument"]:
            qs = qs.filter(study__instrument__name=options["instrument"])
        if options["study"]:
            qs = qs.filter(study_id=options["study"])
        ids = list(qs.values_list("pk", flat=True)[: options["limit"]])
        mismatched = 0
        for pk in ids:
            _, _, differences = compare_administration(pk)
            if differences:
                mismatched += 1
                self.stdout.write(f"administration {pk}:")
                for d in differences[:20]:
                    self.stdout.write(f"  {d}")
        self.stdout.write(
            f"compared {len(ids)} administrations: {mismatched} with differences"
        )
