import datetime

from dateutil.relativedelta import relativedelta

from brookes.models import BrookesCode


def renewal_codes(request):
    if not request.user.is_anonymous:
        from_date = datetime.date.today()
        to_date = datetime.date.today() + relativedelta(months=1)
        codes = BrookesCode.objects.filter(
            researcher=request.user, expiry__gte=from_date, expiry__lte=to_date
        )
        for code in codes:
            if BrookesCode.objects.filter(
                researcher=request.user,
                expiry__gte=to_date,
                instrument_family=code.instrument_family,
            ).exists():
                codes = codes.exclude(pk=code.pk)
        return {"RENEWAL_CODES": codes}
    return {}
