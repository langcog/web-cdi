import json
import logging
import os
import re
from typing import Any, Dict, List

import requests
from cdi_forms.models import Instrument_Forms
from cdi_forms.views.utils import (
    PROJECT_ROOT,
    get_administration_instance,
    has_backpage,
    language_map,
    model_map,
    prefilled_background_form,
    prefilled_cdi_data,
)

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.views.generic import DetailView, UpdateView
from ipware.ip import get_client_ip
from researcher_UI.models import (
    administration,
    administration_data,
    ip_address,
    payment_code,
)

logger = logging.getLogger("debug")


class AdministrationSummaryView(DetailView):
    model = administration
    template_name = "cdi_forms/administration_summary.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)

        # Get form from database
        background_form = prefilled_background_form(self.object)
        ctx["background_form"] = background_form
        try:
            filename = os.path.realpath(
                PROJECT_ROOT + self.object.study.demographic.path
            )
        except:
            filename = "None"
        if has_backpage(filename):
            backpage_background_form = prefilled_background_form(self.object, False)
            ctx["backpage_background_form"] = backpage_background_form
        ctx["gift_code"] = None
        ctx["gift_amount"] = None

        if self.object.study.allow_payment and self.object.bypass is None:
            amazon_urls = {
                "English": {
                    "redeem_url": "http://www.amazon.com/redeem",
                    "legal_url": "http://www.amazon.com/gc-legal",
                },
                "Spanish": {
                    "redeem_url": "http://www.amazon.com/gc/redeem/?language=es_US",
                    "legal_url": "http://www.amazon.com/gc-legal/?language=es_US",
                },
                "French Quebec": {
                    "redeem_url": "http://www.amazon.ca/gc/redeem/?language=fr_CA",
                    "legal_url": "http://www.amazon.ca/gc-legal/?language=fr_CA",
                },
            }
            url_obj = amazon_urls[self.object.study.instrument.language]
            if payment_code.objects.filter(hash_id=self.object.url_hash).exists():
                gift_card = payment_code.objects.get(hash_id=self.object.url_hash)
                ctx["gift_code"] = gift_card.gift_code
                ctx["gift_amount"] = "${:,.2f}".format(gift_card.gift_amount)
                ctx["redeem_url"] = url_obj["redeem_url"]
                ctx["legal_url"] = url_obj["legal_url"]
            else:
                ctx["gift_code"] = "ran out"
                ctx["gift_amount"] = "ran out"
                ctx["redeem_url"] = None
                ctx["legal_url"] = None
        # calculate graph data
        ctx["cdi_items"] = prefilled_cdi_data(self.object)["cdi_items"]
        cdi_items = json.loads(ctx["cdi_items"])
        categories = {}
        
        categories_data = list(
            unicode_csv_reader(
                open(
                    os.path.realpath(
                        settings.BASE_DIR + "/static/data_csv/word_categories.csv"
                    ),
                    encoding="utf8",
                )
            )
        )

        col_names = categories_data[0]
        nrows = len(categories_data)
        get_row = lambda row: categories_data[row]
        categories = {}
        for row in range(1, nrows):
            row_values = get_row(row)
            if len(row_values) > 1:
                if row_values[col_names.index(self.object.study.instrument.name)]:
                    mapped_name = row_values[
                        col_names.index(self.object.study.instrument.name)
                    ]
                else:
                    mapped_name = row_values[col_names.index("id")]
                categories[row_values[col_names.index("id")]] = {
                    "produces": 0,
                    "understands": 0,
                    "count": 0,
                    "mappedName": mapped_name,
                }
        for row in cdi_items:
            if row["item_type"] == "word":
                categories[row["category"]]["count"] += 1

        prefilled_data_list = administration_data.objects.filter(
            administration=self.object
        ).values("item_ID", "value")
        for item in prefilled_data_list:
            instance = Instrument_Forms.objects.get(
                itemID=item["item_ID"], instrument=self.object.study.instrument
            )
            if instance.item_type == "word":
                if item["value"] == "produces":
                    categories[instance.category]["produces"] += 1
                    categories[instance.category]["understands"] += 1
                if item["value"] == "understands":
                    categories[instance.category]["understands"] += 1

        ctx["graph_data"] = categories
        ctx["language_code"] = settings.LANGUAGE_DICT[
            self.object.study.instrument.language
        ]

        return ctx

    def get_template_names(self) -> List[str]:
        if not self.object.completed:
            return ["cdi_forms/expired.html"]
        else:
            if not self.object.scored:
                self.object.scored = True
                self.object.save()
            return ["cdi_forms/administration_summary.html"]

    def get_object(self, queryset=None):
        self.object = administration.objects.get(url_hash=self.kwargs["hash_id"])
        return self.object

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object()
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not self.object.completed:
            return render(
                request, "cdi_forms/administration_expired.html", {}
            )  # Render contact form template

        completed = int(
            request.get_signed_cookie("completed_num", "0")
        )  # If there is a cookie for a previously completed test, get it

        response = super().get(request, *args, **kwargs)
        if self.object.study.allow_payment:
            response.set_signed_cookie("completed_num", completed)
        return response


class AdministrationDetailView(DetailView):
    model = administration
    template_name = "cdi_forms/pdf_administration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prefilled_data = prefilled_cdi_data(self.object)
        for field in prefilled_data:
            context[field] = prefilled_data[field]
        context["language_code"] = settings.LANGUAGE_DICT[
            context["object"].study.instrument.language
        ]
        return context

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)


class AdministrationUpdateView(UpdateView):
    model = administration
    template_name = "cdi_forms/administration_form.html"
    fields = ["id"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["data"] = self.get_section()
        if "contents" in ctx["data"]:
            ctx["contents"] = ctx["data"]["contents"]
        ctx["timer"] = (
            True
            if (timezone.now() - self.object.created_date).total_seconds() / 60.0
            > self.object.study.timing
            else False
        )
        ctx["language_code"] = language_map(self.get_object().study.instrument.language)
        return ctx

    def get_object(self, queryset=None):
        self.object = administration.objects.get(url_hash=self.kwargs["hash_id"])
        return self.object

    def get_instrument(self):
        self.instrument = model_map(self.object.study.instrument.name)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object()
        self.get_instrument()
        if "btn-previous" in request.POST or "previous" in self.kwargs:
            self.goto_previous_page = True
        else:
            self.goto_previous_page = False
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.object.completed:
            return redirect(
                reverse("administration_summary_view", args=(self.object.url_hash,))
            )
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.object.completed:
            return redirect(
                reverse("administration_summary_view", args=(self.object.url_hash,))
            )
        if "btn-save" in request.POST:
            response = self.request.get_full_path()
        if "btn-previous" in request.POST:
            response = reverse(
                "update_administration_section_previous",
                args=(self.object.url_hash, request.POST["previous"], "previous"),
            )
        if "btn-next" in request.POST:
            response = reverse(
                "update_administration_section",
                args=(self.object.url_hash, request.POST["next"]),
            )
        if "btn-back" in request.POST:
            response = reverse("background-info", args=(self.object.backgroundinfo.pk,))
        if "btn-submit" in request.POST:
            # Some studies may require successfully passing a ReCaptcha test for submission. If so, get for a passing response before marking form as complete.
            result = {"success": None}
            recaptcha_response = request.POST.get("g-recaptcha-response", None)
            if recaptcha_response:
                dt = {
                    "secret": settings.RECAPTCHA_PRIVATE_KEY,
                    "response": recaptcha_response,
                }
                r = requests.post(
                    "https://www.google.com/recaptcha/api/siteverify", data=dt
                )
                result = r.json()

            # If study allows for subject payment and has yet to hit its cap on subjects, try to provide the test-taker with a gift card code.
            if self.object.study.allow_payment and self.object.bypass is None:
                if (
                    self.object.study.confirm_completion and result["success"]
                ) or not self.object.study.confirm_completion:
                    if not payment_code.objects.filter(
                        hash_id=self.object.url_hash
                    ).exists():
                        if (
                            self.object.study.name == "Wordful Study (Official)"
                        ):  # for wordful study: if its second admin, give 25 bucks else 5
                            if self.object.repeat_num == 2:
                                # if this subject already has claimed $25: give them $5 this time
                                if payment_code.objects.filter(
                                    hash_id=self.object.url_hash,
                                    gift_amount=25.0,
                                ).exists():
                                    gift_amount_search = 5.0
                                else:
                                    gift_amount_search = 25.0
                            else:
                                gift_amount_search = 5.0
                            given_code = payment_code.objects.filter(
                                hash_id__isnull=True,
                                study=self.object.study,
                                gift_amount=gift_amount_search,
                            ).first()
                        else:
                            given_code = payment_code.objects.filter(
                                hash_id__isnull=True,
                                study=self.object.study,
                            ).first()

                        if given_code:
                            given_code.hash_id = self.object.url_hash
                            given_code.assignment_date = timezone.now()
                            given_code.save()

            # If the study is run by langcoglab and the study allows for subject payments, store the IP address for security purposes
            # if self.object.study.researcher.username == "langcoglab" and self.object.study.allow_payment:
            if self.object.study.allow_payment:
                user_ip = get_client_ip(request)

                if user_ip and user_ip != "None":
                    ip_address.objects.create(
                        study=self.object.study, ip_address=user_ip
                    )
            try:
                filename = os.path.realpath(
                    PROJECT_ROOT + self.object.study.demographic.path
                )
            except:
                filename = "None"
            if has_backpage(filename):
                self.object.completedSurvey = True
                self.object.save()
                response = reverse(
                    "backpage-background-info", args=(self.object.backgroundinfo.pk,)
                )
            else:
                self.object.completed = True
                self.object.save()
                response = reverse(
                    "administration_summary_view", args=(self.object.url_hash,)
                )

        for (
            key
        ) in (
            request.POST
        ):  # Parse responses and individually save each item's response (empty checkboxes or radiobuttons are not saved)
            items = self.instrument.filter(itemID=key)
            if len(items) == 1:
                item = items[0]
                value = request.POST[key]
                if item.choices:
                    choices = map(str.strip, item.choices.choice_set_en.split(";"))
                    if value in choices:
                        administration_data.objects.update_or_create(
                            administration=self.object,
                            item_ID=key,
                            defaults={"value": value},
                        )
                else:
                    if value:
                        administration_data.objects.update_or_create(
                            administration=self.object,
                            item_ID=key,
                            defaults={"value": value},
                        )
        administration.objects.filter(url_hash=self.object.url_hash).update(
            last_modified=timezone.now()
        )

        return redirect(response)

    def get_field_values(self):
        field_values = [
            "itemID",
            "item",
            "item_type",
            "category",
            "definition",
            "choices__choice_set",
            "enabler",
            "enable_response",
        ]
        field_values += [
            "choices__choice_set_"
            + settings.LANGUAGE_DICT[self.object.study.instrument.language]
        ]
        return field_values

    def cdi_items(self, object_group, item_type, prefilled_data, item_id):
        remove_list = []
        for obj in object_group:
            if obj["enabler"]:
                if administration_data.objects.filter(
                    administration=self.object, item_ID=obj["enabler"]
                ).exists():
                    if (
                        not administration_data.objects.get(
                            administration=self.object, item_ID=obj["enabler"]
                        ).value
                        in obj["enable_response"]
                    ):
                        remove_list.append(obj)
                        continue
                else:
                    continue
            if "textbox" in obj["item"]:
                obj["text"] = obj["definition"]
                if obj["itemID"] in prefilled_data:
                    obj["prefilled_value"] = prefilled_data[obj["itemID"]]
            elif item_type == "checkbox":
                obj["prefilled_value"] = obj["itemID"] in prefilled_data
                obj["definition"] = (
                    obj["definition"][0] + obj["definition"][1:]
                    if obj["definition"][0].isalpha()
                    else obj["definition"][0]
                    + obj["definition"][1]
                    + obj["definition"][2:]
                )
                obj["choices"] = obj["choices__choice_set"]

            elif item_type in ["radiobutton", "modified_checkbox"]:
                raw_split_choices = [
                    i.strip() for i in obj["choices__choice_set"].split(";")
                ]

                # split_choices_translated = map(str.strip, [value for key, value in obj.items() if 'choice_set_' in key][0].split(';'))
                split_choices_translated = [
                    value for key, value in obj.items() if "choice_set_" in key
                ][0].split(";")
                prefilled_values = [
                    False
                    if obj["itemID"] not in prefilled_data
                    else x == prefilled_data[obj["itemID"]]
                    for x in raw_split_choices
                ]

                obj["text"] = (
                    obj["definition"][0] + obj["definition"][1:]
                    if obj["definition"][0].isalpha()
                    else obj["definition"][0]
                    + obj["definition"][1]
                    + obj["definition"][2:]
                )

                if (
                    obj["definition"] is not None
                    and obj["definition"].find("\\") >= 0
                    and item_id in ["complexity", "pronoun_usage"]
                ):
                    instruction = re.search("<b>(.+?)</b>", obj["definition"])
                    if instruction:
                        obj_choices = obj["definition"].split(
                            instruction.group(1) + "</b><br />"
                        )[1]
                    else:
                        obj_choices = obj["definition"]
                    # split_definition = map(str.strip, obj_choices.split('\\'))
                    split_definition = obj_choices.split("\\")
                    obj["choices"] = list(
                        zip(split_definition, raw_split_choices, prefilled_values)
                    )
                else:
                    obj["choices"] = list(
                        zip(
                            split_choices_translated,
                            raw_split_choices,
                            prefilled_values,
                        )
                    )
                    if obj["definition"] is not None:
                        obj["text"] = (
                            obj["definition"][0] + obj["definition"][1:]
                            if obj["definition"][0].isalpha()
                            else obj["definition"][0]
                            + obj["definition"][1]
                            + obj["definition"][2:]
                        )

            elif item_type == "textbox":
                if obj["itemID"] in prefilled_data:
                    obj["prefilled_value"] = prefilled_data[obj["itemID"]]

        # now clear out those removed:
        for obj in remove_list:
            object_group.remove(obj)
        return object_group

    def return_data(self, section, item_type, prefilled_data, target="category"):
        raw_objects = []

        if target == "category":
            group_objects = self.instrument.filter(
                category__exact=section["id"]
            ).values(*self.get_field_values())

            section["section"] = {
                "title": None if "title" not in section else section["title"],
                "text": "" if "text" not in section else section["text"],
                "footnote": "" if "footnote" not in section else section["footnote"],
            }

        elif target == "item_type":
            group_objects = self.instrument.filter(
                item_type__exact=item_type["id"]
            ).values(*self.get_field_values())

        if "type" not in section:
            section["type"] = item_type["type"]
        if "type" not in item_type:
            item_type["type"] = section["type"]

        x = self.cdi_items(
            list(group_objects),
            section["type"],
            prefilled_data,
            item_type["id"],
        )
        section["objects"] = x

        if self.object.study.show_feedback:
            raw_objects.extend(x)
        if any(["*" in x["definition"] for x in section["objects"]]):
            section["starred"] = "*Or the word used in your family"

        section["type"] = {
            "title": "" if "title" not in item_type else item_type["title"],
            "subtitle": "" if "sub_title" not in item_type else item_type["sub_title"],
            "type": "" if "type" not in item_type else item_type["type"],
            "instructions": "" if "text" not in item_type else item_type["text"],
            "id": item_type["id"],
        }
        return section

    def max_page(self, contents):
        page = 0
        for part in contents:
            for item in part["types"]:
                if "page" in item:
                    if item["page"] > page:
                        page = item["page"]
                if "sections" in item:
                    for section in item["sections"]:
                        if section["page"] > page:
                            page = section["page"]
        return page

    def get_section(self, target_section=None):
        if not target_section and "section" in self.kwargs:
            target_section = self.kwargs["section"]

        prefilled_data_list = administration_data.objects.filter(
            administration=self.object
        ).values("item_ID", "value")

        if (
            not prefilled_data_list
            and self.object.repeat_num > 1
            and self.object.study.prefilled_data >= 2
        ):
            old_admins = administration.objects.filter(
                study=self.object.study,
                subject_id=self.object.subject_id,
                completed=True,
            )
            word_items = self.instrument.filter(item_type="word").values_list(
                "itemID", flat=True
            )
            if old_admins:
                old_admin = old_admins.latest("last_modified")
                old_admin_data = administration_data.objects.filter(
                    administration=old_admin, item_ID__in=word_items
                ).values("item_ID", "value")
                new_data_objs = []
                for admin_data_obj in old_admin_data:
                    new_data_objs.append(
                        administration_data(
                            administration=self.object,
                            item_ID=admin_data_obj["item_ID"],
                            value=admin_data_obj["value"],
                        )
                    )
                administration_data.objects.bulk_create(new_data_objs)
                prefilled_data_list = administration_data.objects.filter(
                    administration=self.object
                ).values("item_ID", "value")

        prefilled_data = {
            x["item_ID"]: x["value"] for x in prefilled_data_list
        }  # Store prefilled data in a dictionary with item_ID as the key and response as the value.

        with open(
            PROJECT_ROOT
            + "/form_data/"
            + self.object.study.instrument.name
            + "_meta.json",
            "r",
            encoding="utf-8",
        ) as content_file:  # Open associated json file with section ordering and nesting
            # Read json file and store additional variables regarding the instrument, study, and the administration
            data = json.loads(content_file.read())

        for part in data["parts"]:
            for item_type in part["types"]:
                if "page" in item_type:
                    if target_section == item_type["page"]:
                        return_data = self.return_data(
                            item_type, item_type, prefilled_data, target="item_type"
                        )
                        if len(
                            return_data["objects"]
                        ) < 1 and target_section < self.max_page(data["parts"]):
                            new_target = (
                                target_section + 1
                                if not self.goto_previous_page
                                else target_section - 1
                            )
                            return self.get_section(target_section=new_target)
                        return_data["part"] = part["title"]
                        return_data["contents"] = data["parts"]
                        return_data["menu"] = target_section
                        return return_data
                elif "sections" in item_type:
                    for section in item_type["sections"]:
                        if target_section == section["page"]:
                            return_data = self.return_data(
                                section, item_type, prefilled_data
                            )
                            if len(return_data["objects"]) < 1 and target_section:
                                new_target = (
                                    target_section + 1
                                    if not self.goto_previous_page
                                    else target_section - 1
                                )
                                return self.get_section(target_section=new_target)
                            return_data["part"] = part["title"]
                            return_data["contents"] = data["parts"]
                            return_data["menu"] = target_section
                            return return_data
                else:
                    return_data = {}

                    """
                    if self.object.study.show_feedback:
                        raw_objects.extend(x)
                    """


def update_administration_data_item(request):
    if not request.POST:
        return

    hash_id = request.POST.get("hash_id")
    administration_instance = get_administration_instance(hash_id)

    value = ""
    if request.POST["check"] == "true":
        value = request.POST["value"]

    if len(value) > 0:
        administration_data.objects.update_or_create(
            administration=administration_instance,
            item_ID=request.POST["item"],
            defaults={"value": value},
        )
    elif administration_data.objects.filter(
        administration=administration_instance, item_ID=request.POST["item"]
    ).exists():
        administration_data.objects.get(
            administration=administration_instance, item_ID=request.POST["item"]
        ).delete()
    administration.objects.filter(url_hash=hash_id).update(last_modified=timezone.now())
    return HttpResponse(json.dumps([{}]), content_type="application/json")
