import random

from django.urls import reverse


def get_admin_change_view_url(obj: object) -> str:
    return reverse(
        "admin:{}_{}_change".format(obj._meta.app_label, type(obj).__name__.lower()),
        args=(obj.pk,),
    )


def get_admin_changelist_view_url(obj: object) -> str:
    return reverse(
        "admin:{}_{}_changelist".format(
            obj._meta.app_label, type(obj).__name__.lower()
        ),
    )


def random_password(size=8, chars="0123456789abcdefghijklmnopqrstuvwxyz"):
    return "".join(random.choice(chars) for _ in range(size))
