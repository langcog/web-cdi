import json
import os
import re

from typing import Any, Dict
from django import http
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse
from django.utils import timezone, translation
from django.views.generic import DetailView, UpdateView
from researcher_UI.models import administration, administration_data
from cdi_forms.views.utils import prefilled_cdi_data, PROJECT_ROOT, model_map, get_administration_instance, has_backpage, language_map
from django.conf import settings
from cdi_forms.views import printable_view

import logging
logger = logging.getLogger("debug")

class AdministrationSummaryView(DetailView):
    model = administration
    template_name = "cdi_forms/administration_summary.html"

    def get_object(self, queryset=None):
        self.object = administration.objects.get(url_hash=self.kwargs['hash_id'])
        return self.object
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object()
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return printable_view (request, self.object.url_hash)
    

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
    fields = ['id']

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['data'] = self.get_section()
        if 'contents' in ctx['data']:
            ctx['contents'] = ctx['data']['contents']
        ctx['timer'] = True if (timezone.now()-self.object.created_date).total_seconds() / 60.0 > self.object.study.timing else False
        ctx['language_code'] = language_map(self.get_object().study.instrument.language)
        return ctx
    
    def get_object(self, queryset=None):
        self.object = administration.objects.get(url_hash=self.kwargs['hash_id'])
        return self.object
    
    def get_instrument(self):
        self.instrument = model_map(
            self.object.study.instrument.name
        )
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object()
        self.get_instrument()
        logger.debug(f'Kwargs {self.kwargs}')
        if 'btn-previous' in request.POST or 'previous' in self.kwargs:
            self.goto_previous_page=True
        else:
            self.goto_previous_page=False
        language = language_map(self.get_object().study.instrument.language)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.object.completed:
            return redirect(reverse('administration_summary_view', args=(self.object.url_hash,)))
        return super().get(request, *args, **kwargs)
        
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.object.completed:
            return redirect(reverse('administration_summary_view', args=(self.object.url_hash,)))
        if 'btn-save' in request.POST:
            response = self.request.get_full_path()
        if 'btn-previous' in request.POST:
            response = reverse('update_administration_section_previous', args=(self.object.url_hash, request.POST['previous'], 'previous' ))
        if 'btn-next' in request.POST:
            response = reverse('update_administration_section', args=(self.object.url_hash, request.POST['next'] ))
        if 'btn-back' in request.POST:
            response = reverse('background-info', args=(self.object.backgroundinfo.pk,))
        if 'btn-submit' in request.POST:
            try:
                filename = os.path.realpath(
                    PROJECT_ROOT + self.object.study.demographic.path
                )
            except:
                filename = "None"
            if has_backpage(filename):
                self.object.completedSurvey = True
                self.object.save()
                response = reverse("backpage-background-info", args=(self.object.backgroundinfo.pk,))
            else:
                self.object.completed = True
                self.object.save()
                response = reverse('administration_summary_view', args=(self.object.url_hash,))

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
        administration.objects.filter(url_hash=self.object.url_hash).update(last_modified=timezone.now())

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
            "enable_response"
        ]
        field_values += [
            "choices__choice_set_"
            + settings.LANGUAGE_DICT[self.object.study.instrument.language]
        ]
        return field_values
    
    def cdi_items(self, object_group, item_type, prefilled_data, item_id):
        remove_list=[]
        for obj in object_group:
            if obj['enabler']:
                if administration_data.objects.filter(administration=self.object, item_ID=obj['enabler']).exists():
                    if not administration_data.objects.get(administration=self.object, item_ID=obj['enabler']).value in obj['enable_response']:
                        remove_list.append(obj)
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

        #now clear out those removed:
        for obj in remove_list:
            object_group.remove(obj)
        return object_group
    
    def return_data(self, section, item_type, prefilled_data, target='category'):
        raw_objects = []

        if target == 'category':
            group_objects = self.instrument.filter(
                category__exact=section["id"]
            ).values(*self.get_field_values())
                
            section['section'] = {
                'title': None if not 'title' in section else section['title'],
                'text': '' if not 'text' in section else section['text'],
                'footnote': '' if not 'footnote' in section else section['footnote']
            }
            
        elif target == 'item_type':
            group_objects = self.instrument.filter(
                item_type__exact=item_type["id"]
            ).values(*self.get_field_values())
                    
        if 'type' not in section:
            section['type'] = item_type['type']
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

        section['type'] = {
            'title': '' if not 'title' in item_type else item_type['title'],
            'subtitle': '' if not 'sub_title' in item_type else item_type['sub_title'],
            'type': '' if not 'type' in item_type else item_type['type'],
            'instructions': '' if not 'text' in item_type else item_type['text'],
            'id': item_type['id'],
        }
        return section
    
    def get_section(self, target_section=None):
        if not target_section and 'section' in self.kwargs:
            target_section = self.kwargs['section']

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
            PROJECT_ROOT + "/form_data/" + self.object.study.instrument.name + "_meta.json",
            "r",
            encoding="utf-8",
        ) as content_file:  # Open associated json file with section ordering and nesting
            # Read json file and store additional variables regarding the instrument, study, and the administration
            data = json.loads(content_file.read())

        for part in data["parts"]:
            for item_type in part["types"]:
                if 'page' in item_type:
                    if target_section == item_type['page']:
                        return_data = self.return_data(item_type, item_type, prefilled_data, target='item_type')
                        if len(return_data['objects']) < 1:
                            logger.debug(f'Old target is {target_section}')
                            logger.debug(f'Previous Page {self.goto_previous_page}')
                            
                            new_target = target_section+1 if not self.goto_previous_page else target_section-1
                            logger.debug(f'New target is {new_target}')
                            return self.get_section(target_section=new_target)
                        return_data['part'] = part['title']
                        return_data['contents'] = data['parts']
                        return_data['menu'] = target_section
                        return return_data
                elif "sections" in item_type:
                    for section in item_type['sections']:
                        if target_section == section['page']:
                            return_data = self.return_data(section, item_type, prefilled_data)
                            if len(return_data['objects']) < 1:
                                logger.debug(f'Old target is {target_section}')
                                new_target = target_section+1 if not self.goto_previous_page else target_section-1
                                logger.debug(f'New target is {new_target}')
                                return self.get_section(target_section=new_target)
                            return_data['part'] = part['title']
                            return_data['contents'] = data['parts']
                            return_data['menu'] = target_section
                            return return_data
                else:
                    return_data =  {}
                        

                    '''
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