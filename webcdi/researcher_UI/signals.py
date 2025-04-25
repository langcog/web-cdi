import logging
import sys
import requests 

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from cdi_forms.scores import update_summary_scores
# from registration.models import RegistrationProfile
from researcher_UI.models import Administration, Researcher

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
    logger.debug(
        f"pre_save setting __original_completed to { instance.__original_completed }"
    )


@receiver(post_save, sender=Administration)
def post_save_completed_handler(sender, instance, created, **kwargs):
    logger.debug(
        f"post_save: __original_completed is { instance.__original_completed }; completed is {instance.completed}"
    )
    if instance.completed and not instance.__original_completed and not TESTING:
        update_summary_scores(instance)

@receiver(post_save, sender=Administration)
def check_send_completion_flag_url_response(sender, instance, created, **kwargs):
    if instance.study.send_completion_flag_url and instance.completed:
        data = instance.study.completion_data
        for item in data:
            data[item] = (
                data[item]
                .replace(
                    "{{source_id}}",
                    instance.backgroundinfo.source_id or "",
                )
                .replace(
                    "{{event_id}}",
                    instance.backgroundinfo.event_id or "",
                )
                        )
        count = 0
        while instance.send_completion_flag_url_response != 200:
            count += 1
            r = requests.post(
                instance.study.send_completion_flag_url, data=data
            )
            instance.send_completion_flag_url_response = int(r.status_code)
            if count > 5:
                logger.error(
                    f"Failed to get 200 status code for Administration { instance.id } within source_id { instance.backgroundinfo.source_id }"
                )
                break
            