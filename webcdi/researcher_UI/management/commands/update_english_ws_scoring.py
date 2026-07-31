from django.core.management.base import BaseCommand


from researcher_UI.models import InstrumentScore, Instrument


class Command(BaseCommand):


    def handle(self, *args, **options):
        instrument = Instrument.objects.get(name="English_WS")
        try:
            instrument_score=InstrumentScore.objects.get(instrument=instrument, title="Word Forms 2 Nouns")
            instrument_score.title = "Word Endings 2 Nouns"
            instrument_score.save()
        except Exception as e:
            pass

        try:
            instrument_score=InstrumentScore.objects.get(instrument=instrument, title="Word Forms 2 Verbs")
            instrument_score.title = "Word Endings 2 Verbs"
            instrument_score.save()
        except Exception as e:
                pass