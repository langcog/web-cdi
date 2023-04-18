from django.conf import settings


def home_page(request):
    return {
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "MORE_INFO_LINK": settings.MORE_INFO_ADDRESS,
    }
