# Generated by Django 3.2.18 on 2023-04-03 15:38

from django.db import migrations, models

def update_researchers(apps, schema_editor):
    Researcher = apps.get_model('researcher_UI', 'researcher')
    
    for researcher in Researcher.objects.all():
        for instrument in researcher.allowed_instruments.all():
            if instrument.family and not instrument.family in researcher.allowed_instrument_families.all():
                try:
                    researcher.allowed_instrument_families.add(instrument.family)
                except Exception as e:
                    print(f'Failed to add family for instrument {instrument} to {researcher.user}.  Error {e}')

class Migration(migrations.Migration):

    dependencies = [
        ('researcher_UI', '0069_instrument_family'),
    ]

    operations = [
        migrations.AddField(
            model_name='researcher',
            name='allowed_instrument_families',
            field=models.ManyToManyField(blank=True, to='researcher_UI.InstrumentFamily', verbose_name='Instrument Families this researcher has access to'),
        ),
        migrations.RunPython(update_researchers)
    ]