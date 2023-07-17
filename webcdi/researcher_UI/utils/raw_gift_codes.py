import logging
import re
from decimal import Decimal

from researcher_UI.models import payment_code

logger = logging.getLogger("debug")


def raw_gift_code_fun(raw_gift_amount, study_obj, new_study_name, raw_gift_codes):
    all_new_codes = None
    amount_regex = None
    data = {}
    if raw_gift_codes:
        new_payment_codes = []
        used_codes = []
        gift_codes = re.split("[,;\s\t\n]+", raw_gift_codes)
        gift_regex = re.compile(r"^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{4}$")
        gift_type = "Amazon"
        gift_codes = filter(gift_regex.search, gift_codes)

        try:
            amount_regex = Decimal(raw_gift_amount.replace("$", ""))
        except:
            pass

        if amount_regex:
            for gift_code in gift_codes:
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
                else:
                    used_codes.append(gift_code)

        if not used_codes:
            all_new_codes = True

    if raw_gift_codes:
        if not all_new_codes or not amount_regex:
            data["stat"] = "error"
            err_msg = []
            if not all_new_codes:
                err_msg = (
                    err_msg
                    + ["The following codes are already in the database:"]
                    + used_codes
                )
            if not amount_regex:
                err_msg = err_msg + [
                    'Please enter in a valid amount for "Amount per Card"'
                ]

            data["error_message"] = "<br>".join(err_msg)

        else:
            if all_new_codes:
                payment_code.objects.bulk_create(new_payment_codes)
                data["stat"] = "ok"
    else:
        data["stat"] = "ok"

    return data
