import logging
import sys

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from cdi_forms.scores import update_summary_scores
from researcher_UI.models import Administration, Researcher
from researcher_UI.utils.completion_notice import send_completion_notice

logger = logging.getLogger("debug")

TESTING = sys.argv[1:2] == ["test"]


@receiver(post_save, sender=Researcher)
def update_instruments(sender, instance, **kwargs):
    """
    Brings instruments for a researcher up to date on save
    """
    for instrument in instance.allowed_instruments.all():
        instance.allowed_instruments.remove(instrument)
    for family in instance.allowed_instrument_families.all():
        for instrument in family.instrument_set.all():
            instance.allowed_instruments.add(instrument)


m2m_changed.connect(
    update_instruments,
    sender=Researcher.allowed_instrument_families.through,
)


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Researcher.objects.get_or_create(user=instance)
        instance.is_active = True
        instance.save()


@receiver(pre_save, sender=Administration)
def cache_previous_completed(sender, instance, *args, **kwargs):
    original_completed = None
    if instance.id and not TESTING:
        original_completed = Administration.objects.get(pk=instance.id).completed
    instance.__original_completed = original_completed


@receiver(post_save, sender=Administration)
def post_save_completed_handler(sender, instance, created, **kwargs):
    if instance.completed and not instance.__original_completed and not TESTING:
        update_summary_scores(instance)


@receiver(pre_save, sender=Administration)
def flag_completion_notice(sender, instance, **kwargs):
    """Mark an existing administration that is becoming completed.

    The flag is only ever set here and cleared by send_completion_notice_handler,
    so a nested save (e.g. scoring from post_save_completed_handler) can't
    hide the transition or send the notice twice. Newly created, already
    completed administrations (data imports) are not notified.
    """
    if (
        not kwargs.get("raw")
        and instance.completed
        and instance.id
        and instance.study.send_completion_flag_url
        and Administration.objects.filter(pk=instance.id, completed=False).exists()
    ):
        instance._completion_notice_due = True


@receiver(post_save, sender=Administration)
def send_completion_notice_handler(sender, instance, created, **kwargs):
    if getattr(instance, "_completion_notice_due", False):
        instance._completion_notice_due = False
        # retries, if needed, are made by crontab_scoring
        transaction.on_commit(lambda: send_completion_notice(instance))
