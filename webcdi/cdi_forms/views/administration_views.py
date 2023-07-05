import json
from typing import Any, Dict, Optional
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.views.generic import DetailView, UpdateView
from researcher_UI.models import administration, administration_data

from cdi_forms.views.utils import prefilled_cdi_data, PROJECT_ROOT, model_map, cdi_items, get_administration_instance
from cdi_forms.utils import previous_and_next
from django.conf import settings

import logging
logger = logging.getLogger("debug")

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
        if 'contents' in ctx['data']:
            ctx['contents'] = ctx['data']['contents']
        return ctx
    
    def get_object(self, queryset=None):
        return administration.objects.get(url_hash=self.kwargs['hash_id'])
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if 'btn-save' in request.POST:
            response = self.request.get_full_path()
        if 'btn-previous' in request.POST:
            response = reverse('update_administration_section', args=(self.get_object().url_hash, request.POST['previous'] ))
        if 'btn-next' in request.POST:
            response = reverse('update_administration_section', args=(self.get_object().url_hash, request.POST['next'] ))
        if 'btn-back' in request.POST:
            response = reverse('background-info', args=(self.get_object().backgroundinfo.pk,))

        administration.objects.filter(url_hash=self.get_object().url_hash).update(last_modified=timezone.now())

        return redirect(response)
    
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
    
    def return_data(self, section, item_type, prefilled_data, target='category'):
        raw_objects = []
        instrument_model = model_map(
            self.object.study.instrument.name
        )
        if target == 'category':
            group_objects = instrument_model.filter(
                category__exact=section["id"]
            ).values(*self.get_field_values())
            
        elif target == 'item_type':
            group_objects = instrument_model.filter(
                item_type__exact=item_type["id"]
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
            for previous_type, item_type, next_type in previous_and_next(part["types"]):
                if "sections" in item_type:
                    for previous_section, section, next_section in previous_and_next(item_type['sections']):
                        if target_section == None or target_section == section['id']:
                            return_data =  self.return_data(section, item_type, prefilled_data)
                            return_data['part'] = part['title']
                            if 'sub_title' in item_type:
                                subtitle = item_type['sub_title']
                            else:
                                subtitle = ''
                            return_data['type'] = {
                                'title': item_type['title'],
                                'subtitle': subtitle,
                                'type': item_type['type'],
                                'instructions': item_type['text'],
                                'id': item_type['id'],
                            }
                            return_data['contents'] = data['parts']
                            if previous_section:
                                return_data['previous_section'] = previous_section['id']
                            else:
                                return_data['previous_section'] = None
                            if next_section:
                                return_data['next_section'] = next_section['id']
                            elif next_type:
                                return_data['next_section'] = next_type['id']
                            else:
                                return_data['next_section'] = None
                            return return_data
                    '''
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
                    '''
                else:
                    logger.debug (f'IN ELSE SECTION')
                    if target_section == item_type['id']:
                        continue
                        return_data =  self.return_data(section, item_type, prefilled_data)
                        return_data['part'] = part['title']
                        if 'sub_title' in item_type:
                            subtitle = item_type['sub_title']
                        else:
                            subtitle = ''
                        
                        instructions = item_type['text'] if 'text' in item_type else None
                        return_data['type'] = {
                            'title': item_type['title'],
                            'subtitle': subtitle,
                            'type': item_type['type'],
                            'instructions': instructions,
                            'id': item_type['id'],
                        }
                        return_data['contents'] = data['parts']
                        if previous_section:
                            return_data['previous_section'] = previous_section['id']
                        else:
                            return_data['previous_section'] = None
                        if next_section:
                            return_data['next_section'] = next_section['id']
                        elif next_type:
                            return_data['next_section'] = next_type['id']
                        else:
                            return_data['next_section'] = None
                        return return_data
                    '''
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
                    '''

def update_administration_data_item(request):
    if not request.POST:
        return

    hash_id = request.POST.get("hash_id")
    administration_instance = get_administration_instance(hash_id)
    instrument_name = (
        administration_instance.study.instrument.name
    )  # Get instrument name associated with study
    instrument_model = model_map(instrument_name).filter(
        itemID__in=request.POST
    )  # Fetch instrument model based on instrument name.

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