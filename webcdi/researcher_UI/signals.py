from django.db.models.signals import post_save
from django.dispatch import receiver

from registration.models import RegistrationProfile

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
            'webmaster@localhost.com',
            [settings.USER_ADMIN_EMAIL],
            fail_silently=False,
        )

