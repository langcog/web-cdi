# Staging-only: stop a real-data copy from reaching the outside world (#687)
from django.conf import settings
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Concat
from researcher_UI.models import Study, PaymentCode
assert settings.DATABASES["default"]["HOST"].startswith("/cloudsql/"), "refusing: not Cloud SQL"
with transaction.atomic():
    n1 = Study.objects.exclude(send_completion_flag_url__isnull=True).exclude(send_completion_flag_url="").update(send_completion_flag_url=None)
    json_redirect = Study.objects.filter(redirect_boolean=True, direct_redirect_boolean=False).exclude(redirect_url__isnull=True).exclude(redirect_url="")
    n2 = json_redirect.update(redirect_url="")
    n3 = PaymentCode.objects.update(gift_code=Concat(Value("STAGING-TEST-"), F("id")))
print("CHECK scrubbed: completion-flag URLs", n1, "| server-side redirect URLs", n2, "| gift codes replaced", n3)
