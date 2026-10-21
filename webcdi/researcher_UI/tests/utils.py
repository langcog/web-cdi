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


class LiveServerFixturesMixin:
    """For LiveServerTestCase classes that load the test fixtures (#648).

    After each test the database is flushed and post_migrate re-creates the
    content types under new ids, so the next test's fixtures (which carry
    their own content types and permissions) collide on the unique
    (app_label, model) constraint. Start each test without them.
    """

    @classmethod
    def _fixture_setup(cls):
        from django.contrib.contenttypes.models import ContentType

        ContentType.objects.all().delete()  # cascades to permissions, log entries
        ContentType.objects.clear_cache()
        super()._fixture_setup()
