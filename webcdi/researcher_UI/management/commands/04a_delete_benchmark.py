import json
import re
from django.core.management.base import BaseCommand

from researcher_UI.models import Benchmark

class Command(BaseCommand):
    def handle(self, *args, **options):
        Benchmark.objects.all().delete()

        