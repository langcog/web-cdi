import logging
import re
from decimal import Decimal

from django.utils.safestring import mark_safe
from django.contrib import messages
from researcher_UI.models import PaymentCode

logger = logging.getLogger("debug")

def get_gift_card_regex(gift_type):
    if gift_type == "Amazon":
        return re.compile(r"^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{4}$")
    if gift_type == 'Tango':
         return re.compile(r"^[A-Z]{2}[0-9]{6}-[0-9]{7}-[0-9]{2}-[0-9]{1}$")
    return re.compile(r"^[A-Za-z0-9-]+$")

def raw_gift_code_fun(request, gift_type, raw_gift_amount, study_obj, new_study_name, raw_gift_codes):
    amount_regex = None
    
    if raw_gift_codes:
        gift_codes = re.split("[,;\s\t\n]+", raw_gift_codes)
        gift_type = gift_type
        gift_regex = get_gift_card_regex(gift_type)

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
                if not PaymentCode.objects.filter(
                    payment_type=gift_type, gift_code=gift_code
                ).exists():
                    new_payment_codes.append(
                        PaymentCode(
                            study=study_obj,
                            payment_type=gift_type,
                            gift_code=gift_code,
                            gift_amount=amount_regex,
                        )
                    )
                    new_codes.append(gift_code)
                else:
                    used_codes.append(gift_code)
            PaymentCode.objects.bulk_create(new_payment_codes)

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

    return
