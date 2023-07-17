import json
import logging
import os
import re
from pathlib import Path

from cdi_forms.models import BackgroundInfo, Instrument_Forms, Zipcode
from django.conf import settings
from django.http import Http404
from django.utils import translation
from researcher_UI.models import administration, administration_data, instrument
from cdi_forms.forms import BackgroundForm, BackpageBackgroundForm

logger = logging.getLogger("debug")

PROJECT_ROOT = str(
    Path(os.path.dirname(__file__)).parent.absolute()
)  # Declare root folder for project and files. Varies between Mac and Linux installations.


# This function is not written properly...
def language_map(language):
    with translation.override("en"):
        available_langs = dict(settings.LANGUAGES)
        trimmed_lang = re.sub(r"(\s+)?\([^)]*\)", "", language).strip()
        lang_code = None

        for code, language in available_langs.items():
            if language == trimmed_lang:
                lang_code = code

        assert lang_code, (
            "'%s' not available in language mapping function (language_map, cdi_forms/views.py)"
            % trimmed_lang
        )
        return lang_code


def has_backpage(filename):
    back_page = 0
    if os.path.isfile(filename):
        pages = json.load(open(filename, encoding="utf-8"))
        for page in pages:
            if page["page"] == "back":
                back_page = 1
    return back_page


# Map name of instrument model to its string title
def model_map(name):
    assert instrument.objects.filter(name=name).exists(), (
        "%s is not registered as a valid instrument" % name
    )
    instrument_obj = instrument.objects.get(name=name)
    cdi_items = Instrument_Forms.objects.filter(instrument=instrument_obj).order_by(
        "item_order"
    )

    assert cdi_items.count() > 0, (
        "Could not find any CDI items registered with this instrument: %s" % name
    )
    return cdi_items


# Prepare items with prefilled reponses for later rendering. Dependent on cdi_items
def prefilled_cdi_data(administration_instance):
    prefilled_data_list = administration_data.objects.filter(
        administration=administration_instance
    ).values(
        "item_ID", "value"
    )  # Grab a list of prefilled responses
    instrument_name = (
        administration_instance.study.instrument.name
    )  # Grab instrument name
    instrument_model = model_map(
        instrument_name
    )  # Grab appropriate model given the instrument name associated with test

    if (
        not prefilled_data_list
        and administration_instance.repeat_num > 1
        and administration_instance.study.prefilled_data >= 2
    ):
        word_items = instrument_model.filter(item_type="word").values_list(
            "itemID", flat=True
        )
        old_admins = administration.objects.filter(
            study=administration_instance.study,
            subject_id=administration_instance.subject_id,
            completed=True,
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
                        administration=administration_instance,
                        item_ID=admin_data_obj["item_ID"],
                        value=admin_data_obj["value"],
                    )
                )
            administration_data.objects.bulk_create(new_data_objs)
            prefilled_data_list = administration_data.objects.filter(
                administration=administration_instance
            ).values("item_ID", "value")

    prefilled_data = {
        x["item_ID"]: x["value"] for x in prefilled_data_list
    }  # Store prefilled data in a dictionary with item_ID as the key and response as the value.
    with open(
        PROJECT_ROOT + "/form_data/" + instrument_name + "_meta.json",
        "r",
        encoding="utf-8",
    ) as content_file:  # Open associated json file with section ordering and nesting
        # Read json file and store additional variables regarding the instrument, study, and the administration
        data = json.loads(content_file.read())
        data["object"] = administration_instance
        data["title"] = administration_instance.study.instrument.verbose_name
        instrument_name = data[
            "instrument_name"
        ] = administration_instance.study.instrument.name
        data["completed"] = administration_instance.completed
        data["due_date"] = administration_instance.due_date.strftime(
            "%b %d, %Y, %I:%M %p"
        )
        data["page_number"] = administration_instance.page_number
        data["hash_id"] = administration_instance.url_hash
        data["study_waiver"] = administration_instance.study.waiver
        data["confirm_completion"] = administration_instance.study.confirm_completion

        try:
            data["back_page"] = has_backpage(
                PROJECT_ROOT + administration_instance.study.demographic.path
            )
        except:
            data["back_page"] = 0

        raw_objects = []

        field_values = [
            "itemID",
            "item",
            "item_type",
            "category",
            "definition",
            "choices__choice_set",
        ]
        field_values += [
            "choices__choice_set_"
            + settings.LANGUAGE_DICT[administration_instance.study.instrument.language]
        ]

        # As some items are nested on different levels, carefully parse and store items for rendering.
        for part in data["parts"]:
            for item_type in part["types"]:
                if "sections" in item_type:
                    for section in item_type["sections"]:
                        group_objects = instrument_model.filter(
                            category__exact=section["id"]
                        ).values(*field_values)
                        if "type" not in section:
                            section["type"] = item_type["type"]
                        x = cdi_items(
                            group_objects,
                            section["type"],
                            prefilled_data,
                            item_type["id"],
                        )
                        section["objects"] = x
                        if administration_instance.study.show_feedback:
                            raw_objects.extend(x)
                        if any(["*" in x["definition"] for x in section["objects"]]):
                            section["starred"] = "*Or the word used in your family"

                else:
                    group_objects = instrument_model.filter(
                        item_type__exact=item_type["id"]
                    ).values(*field_values)
                    x = cdi_items(
                        group_objects,
                        item_type["type"],
                        prefilled_data,
                        item_type["id"],
                    )
                    item_type["objects"] = x
                    if administration_instance.study.show_feedback:
                        raw_objects.extend(x)
        # print (raw_objects)
        data["cdi_items"] = json.dumps(raw_objects)  # , cls=DjangoJSONEncoder)

        # If age is stored in database, add it to dictionary
        try:
            age = BackgroundInfo.objects.values_list("age", flat=True).get(
                administration=administration_instance
            )
        except:
            age = ""
        data["age"] = age
    return data


# Stitch section nesting in cdi_forms/form_data/*.json and instrument models together and prepare for CDI form rendering
def cdi_items(object_group, item_type, prefilled_data, item_id):
    for obj in object_group:
        if "textbox" in obj["item"]:
            obj["text"] = obj["definition"]
            if obj["itemID"] in prefilled_data:
                obj["prefilled_value"] = prefilled_data[obj["itemID"]]
        elif item_type == "checkbox":
            obj["prefilled_value"] = obj["itemID"] in prefilled_data
            # print ( obj['itemID'] )
            obj["definition"] = (
                obj["definition"][0] + obj["definition"][1:]
                if obj["definition"][0].isalpha()
                else obj["definition"][0] + obj["definition"][1] + obj["definition"][2:]
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
                else obj["definition"][0] + obj["definition"][1] + obj["definition"][2:]
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
                    zip(split_choices_translated, raw_split_choices, prefilled_values)
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

    return object_group


def safe_harbor_zip_code(obj):
    zip_prefix = ""
    raw_zip = obj.zip_code
    if raw_zip and raw_zip != "None":
        zip_prefix = raw_zip[:3]
        if Zipcode.objects.filter(zip_prefix=zip_prefix).exists():
            zip_prefix = Zipcode.objects.filter(zip_prefix=zip_prefix).first().state
        else:
            zip_prefix = zip_prefix + "**"
    return zip_prefix


# Find the administration object for a test-taker based on their unique hash code.
def get_administration_instance(hash_id):
    try:
        administration_instance = administration.objects.get(url_hash=hash_id)
    except:
        raise Http404("Administration not found")
    return administration_instance

# If the BackgroundInfo model was filled out before, populate BackgroundForm with responses based on administation object
def prefilled_background_form(administration_instance, front_page=True):
    background_instance = BackgroundInfo.objects.get(
        administration=administration_instance
    )

    context = {}
    context["language"] = administration_instance.study.instrument.language
    context["instrument"] = administration_instance.study.instrument.name
    context["min_age"] = administration_instance.study.min_age
    context["max_age"] = administration_instance.study.max_age
    context["birthweight_units"] = administration_instance.study.birth_weight_units
    context["study_obj"] = administration_instance.study
    context["study"] = administration_instance.study
    context["source_id"] = administration_instance.backgroundinfo.source_id

    if front_page:
        background_form = BackgroundForm(
            instance=background_instance, context=context, page="front"
        )
    else:
        background_form = BackpageBackgroundForm(
            instance=background_instance, context=context, page="back"
        )
    return background_form