import json
from typing import Any, Dict, Optional
from django.db import models

from django.views.generic import DetailView, UpdateView
from researcher_UI.models import administration, administration_data

from cdi_forms.views.utils import prefilled_cdi_data, PROJECT_ROOT, model_map, cdi_items
from django.conf import settings


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
    

class AdministrationUpdateView(UpdateView):
    model = administration
    template_name = "cdi_forms/administration_form.html"
    fields = ['id']

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['data'] = self.get_section()
        return ctx
    
    def get_object(self, queryset=None):
        return administration.objects.get(url_hash=self.kwargs['hash_id'])
        return super().get_object(queryset)
    
    def get_field_values(self):
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
            + settings.LANGUAGE_DICT[self.object.study.instrument.language]
        ]
        return field_values
    
    def return_data(self, section, item_type, prefilled_data):
        raw_objects = []
        instrument_model = model_map(
            self.object.study.instrument.name
        )
        group_objects = instrument_model.filter(
            category__exact=section["id"]
        ).values(*self.get_field_values())
        if "type" not in section:
            section["type"] = item_type["type"]

        x = cdi_items(
            group_objects,
            section["type"],
            prefilled_data,
            item_type["id"],
        )
        section["objects"] = x

        if self.object.study.show_feedback:
            raw_objects.extend(x)
        if any(["*" in x["definition"] for x in section["objects"]]):
            section["starred"] = "*Or the word used in your family"
            
        return section

    def get_section(self, target_section=None):
        if 'section' in self.kwargs:
            target_section = self.kwargs['section']

        instrument_model = model_map(
            self.object.study.instrument.name
        )
        old_admins = administration.objects.filter(
            study=self.object.study,
            subject_id=self.object.subject_id,
            completed=True,
        )
        word_items = instrument_model.filter(item_type="word").values_list(
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
            PROJECT_ROOT + "/form_data/" + self.object.study.instrument.name + "_meta.json",
            "r",
            encoding="utf-8",
        ) as content_file:  # Open associated json file with section ordering and nesting
            # Read json file and store additional variables regarding the instrument, study, and the administration
            data = json.loads(content_file.read())

        raw_objects = []
        for part in data["parts"]:
            for item_type in part["types"]:
                if "sections" in item_type:
                    for section in item_type["sections"]:
                        if target_section == None:
                            return self.return_data(section, item_type, prefilled_data)
                        if section == target_section:
                            return self.return_data(section, item_type, prefilled_data)
                            
                else:
                    group_objects = instrument_model.filter(
                        item_type__exact=item_type["id"]
                    ).values(*self.get_field_values())
                    x = cdi_items(
                        group_objects,
                        item_type["type"],
                        prefilled_data,
                        item_type["id"],
                    )
                    item_type["objects"] = x
                    if self.object.study.show_feedback:
                        raw_objects.extend(x)
        