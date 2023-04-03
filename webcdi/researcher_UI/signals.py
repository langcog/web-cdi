from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from registration.models import RegistrationProfile
from researcher_UI.models import researcher

from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.conf import settings

@receiver(post_save, sender=RegistrationProfile)
def notify_admin(sender, instance, created, **kwargs):
    '''
    The purpose of this signal is to tell the User Administrator
    (as specified in settings.USER_ADMIN_EMAIL)
    that a new User has applied.ArithmeticError.
    '''
    if created : 
        send_mail(
            Site.objects.get_current().name + ' new registration',
            instance.user.username + ' has registered - please review registration. \n\n' + \
                'https://' + Site.objects.get_current().domain + '/wcadmin/registration/registrationprofile/' ,
            settings.DEFAULT_FROM_EMAIL,
            [settings.USER_ADMIN_EMAIL],
            fail_silently=False,
        )

@receiver(post_save, sender=researcher)
def update_instruments(sender, instance, **kwargs):
    '''
    Brings instruments for a researcher up to date on save
    '''
    for instrument in instance.allowed_instruments.all():
        instance.allowed_instruments.remove(instrument)
    for family in instance.allowed_instrument_families.all():
        for instrument in family.instrument_set.all():
            instance.allowed_instruments.add(instrument)

m2m_changed.connect(
    update_instruments,
    sender=researcher.allowed_instrument_families.through,
)