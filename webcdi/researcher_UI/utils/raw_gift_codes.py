import logging
import re
from decimal import Decimal

from django.utils.safestring import mark_safe
from django.contrib import messages
from researcher_UI.models import payment_code

logger = logging.getLogger("debug")


def raw_gift_code_fun(request, raw_gift_amount, study_obj, new_study_name, raw_gift_codes):
    all_new_codes = None
    amount_regex = None
    data = {}
    if raw_gift_codes:
        gift_codes = re.split("[,;\s\t\n]+", raw_gift_codes)
        gift_regex = re.compile(r"^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{4}$")
        gift_type = "Amazon"

        # Get valid codes
        valid_gift_codes = []
        invalid_gift_codes = []
        for gift_code in gift_codes:
            if gift_regex.search(gift_code):
                valid_gift_codes.append(gift_code)
            else:
                invalid_gift_codes.append(gift_code)
            
        if len(invalid_gift_codes) > 0:
            messages.error(
                request,
                mark_safe(
                    f"The following codes are invalid: {invalid_gift_codes}."
                ),
            )
        
        try:
            amount_regex = Decimal(raw_gift_amount.replace("$", ""))
        except:
            pass

        if amount_regex:
            new_payment_codes = []
            used_codes = []
            new_codes = []
            for gift_code in valid_gift_codes:
                if not payment_code.objects.filter(
                    payment_type=gift_type, gift_code=gift_code
                ).exists():
                    new_payment_codes.append(
                        payment_code(
                            study=study_obj,
                            payment_type=gift_type,
                            gift_code=gift_code,
                            gift_amount=amount_regex,
                        )
                    )
                    new_codes.append(gift_code)
                else:
                    used_codes.append(gift_code)
            payment_code.objects.bulk_create(new_payment_codes)

            if len(used_codes) > 0:
                messages.warning(
                    request,
                    mark_safe(
                        f"The following codes are previously used: {used_codes}"
                    ),
                )
            if len(new_codes) > 0:
                messages.success(
                    request,
                    mark_safe(
                        f"The following codes have been added: {new_codes}"
                    ),
                )
        else:
            messages.error(
                request,
                mark_safe(
                    f"The amount {raw_gift_amount} is invalid"
                ),
            )

        if not used_codes:
            all_new_codes = True

    return
