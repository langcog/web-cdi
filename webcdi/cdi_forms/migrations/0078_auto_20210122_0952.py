# Generated by Django 2.2.13 on 2021-01-22 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0077_auto_20210122_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='backgroundinfo',
            name='child_asks_for_reading',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how many times per week does your child ask to be read to?'),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='child_asks_words_say',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how often does your child ask you what printed words say?'),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='child_self_reads',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how many times per week does your child look at books by himself/herself?'),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='read_at_home',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how many times per week do you read to your child at home?'),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='read_for_pleasure',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how often do you read for fun and pleasure?'),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='rhyming_games',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how often do you play rhyming games with your child?'),
        ),
        migrations.AddField(
            model_name='backgroundinfo',
            name='teach_alphbet',
            field=models.CharField(blank=True, choices=[('never', 'Never'), ('less than once/week', 'Less Than Once/Week'), ('once/week', 'Once/Week'), ('2-3 times/week', '2-3 Times/Week'), ('3-4 times/week', '3-4 Times/Week'), ('5-6 times/week', '5-6 Times/Week'), ('daily', 'Daily')], max_length=51, null=True, verbose_name='About how often do you try to teach your child the letters of the alphabet?'),
        ),
    ]