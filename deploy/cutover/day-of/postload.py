from researcher_UI.models import Instrument
names = sorted(Instrument.objects.filter(family__isnull=True).values_list("name", flat=True))
print("CHECK familyless instruments (expect the 15 retired ones):", len(names), names)
print("CHECK instruments:", Instrument.objects.count())
