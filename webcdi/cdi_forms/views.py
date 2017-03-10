# -*- coding: utf-8 -*-

from django.shortcuts import render
from .models import English_WS, English_WG, BackgroundInfo, requests_log
import os.path
import json
from researcher_UI.models import administration_data, administration, study
from django.http import Http404
import datetime
from .forms import BackgroundForm, ContactForm
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
import itertools
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.contrib import messages



PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def model_map(name):
    mapping = {"English_WS": English_WS, "English_WG": English_WG}
    assert name in mapping, name+"instrument not added to the mapping in views.py model_map function"
    return mapping[name]
        
def get_model_header(name):
    return list(model_map(name).objects.values_list('itemID', flat=True))
    
def prefilled_background_form(administration_instance):
    background_instance = BackgroundInfo.objects.get(administration = administration_instance)
    #age = background_instance.age
    #age_in_date = datetime.date(age/12, age%12, 1)
    #child_dob = datetime.date.today() - age_in_date
    #background_form = BackgroundForm(instance = background_instance, initial={'child_dob':child_dob})  
    background_form = BackgroundForm(instance = background_instance)  
    return background_form

def get_administration_instance(hash_id):
    try:
        administration_instance = administration.objects.get(url_hash = hash_id)
    except:
        raise Http404("Administration not found")
    return administration_instance

def background_info_form(request, hash_id):
    administration_instance = get_administration_instance(hash_id)
    age_ref = {}
    age_ref['language'] = administration_instance.study.instrument.language
    age_ref['instrument'] = administration_instance.study.instrument.name
    age_ref['min_age'] = administration_instance.study.instrument.min_age
    age_ref['max_age'] = administration_instance.study.instrument.max_age
    age_ref['child_age'] = None
    refresh = False
    background_form = None
        
    if request.method == 'POST' :
        if not administration_instance.completed and administration_instance.due_date > timezone.now():
            try:
                background_instance = BackgroundInfo.objects.get(administration = administration_instance)
                if background_instance.age:
                    age_ref['child_age'] = background_instance.age
                background_form = BackgroundForm(request.POST, instance = background_instance, age_ref = age_ref)
            except:
                background_form = BackgroundForm(request.POST, age_ref = age_ref)

            if background_form.is_valid():
                background_instance = background_form.save(commit = False)
                child_dob = background_form.cleaned_data.get('child_dob')
                # # #age = (datetime.date.today() - background_form.cleaned_data.get('child_dob'))
                # # #age = age.year*12 + age.month + (age.day >= 15)
                if child_dob:
                    day_diff = datetime.date.today().day - child_dob.day
                    age = (datetime.date.today().year - child_dob.year) * 12 +  (datetime.date.today().month - child_dob.month) + (1 if day_diff >=15 else 0)
                else:
                    age = None
                # # #validity of age is checked in the modelform's clean method
                if age:
                    background_instance.age = age
                #background_instance.age = background_form.cleaned_data.get('age')
                background_instance.administration = administration_instance
                background_instance.save()
                if 'btn-save' in request.POST and request.POST['btn-save'] == 'Save':
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                    refresh = True
                elif 'btn-next' in request.POST and request.POST['btn-next'] == 'Next':
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                    administration.objects.filter(url_hash = hash_id).update(completedBackgroundInfo = True)
                    request.method = "GET"
                    return cdi_form(request, hash_id)

    if request.method == 'GET' or refresh:
        try:
            #Get form from database
            background_instance = BackgroundInfo.objects.get(administration = administration_instance)
            if background_instance.age:
                age_ref['child_age'] = background_instance.age
            background_form = BackgroundForm(instance = background_instance, age_ref = age_ref)
        except:
            #Blank form
            background_form = BackgroundForm(age_ref = age_ref)  
    data = {}
    data['background_form'] = background_form
    data['hash_id'] = hash_id
    data['completed'] = administration_instance.completed
    data['due_date'] = administration_instance.due_date
    data['language'] = administration_instance.study.instrument.language
    data['title'] = administration_instance.study.instrument.verbose_name
    data['max_age'] = administration_instance.study.instrument.max_age
    data['min_age'] = administration_instance.study.instrument.min_age
    data['study_waiver'] = administration_instance.study.waiver
    study_name = administration_instance.study.name
    study_group = administration_instance.study.study_group
    if study_group:
        data['study_group'] = study_group
        data['alt_study_info'] = study.objects.filter(study_group = study_group).exclude(name = study_name).values_list("name","instrument__min_age", "instrument__max_age", "instrument__language")
    else:
        data['study_group'] = None
        data['alt_study_info'] = None
    return render(request, 'cdi_forms/background_info.html', data)

def cdi_items(object_group, item_type, prefilled_data, item_id):
    for obj in object_group:
        if item_type == 'checkbox':
            obj['prefilled_value'] = obj['itemID'] in prefilled_data
            if obj['gloss'] is None:
                obj['gloss'] = obj['definition']

        if item_type == 'radiobutton' or item_type == 'modified_checkbox':
            split_choices = map(unicode.strip, obj['choices'].split(';'))
            prefilled_values = [False if obj['itemID'] not in prefilled_data else x == prefilled_data[obj['itemID']] for x in split_choices]
            obj['text'] = obj['gloss']

            if obj['definition'] is not None and obj['definition'].find('/') >= 0 and item_id != 'word':
                split_definition = map(unicode.strip, obj['definition'].split('/'))
                obj['choices'] = zip(split_definition, split_choices, prefilled_values)
            else:
                obj['choices'] = zip(split_choices, split_choices, prefilled_values)
                if obj['definition'] is not None:
                    obj['text'] = obj['definition']

        if item_type == 'textbox':
            if obj['itemID'] in prefilled_data:
                obj['prefilled_value'] = prefilled_data[obj['itemID']]
                # print obj['prefilled_value']

    return object_group 


def prefilled_cdi_data(administration_instance):
    prefilled_data_list = administration_data.objects.filter(administration = administration_instance).values('item_ID', 'value')
    instrument_name = administration_instance.study.instrument.name
    instrument_model = model_map(instrument_name)
    prefilled_data = {x['item_ID']: x['value'] for x in prefilled_data_list}
    with open(PROJECT_ROOT+'/form_data/'+instrument_name+'_meta.json', 'r') as content_file:
        data = json.loads(content_file.read())
        data['title'] = administration_instance.study.instrument.verbose_name
        data['instrument_name'] = administration_instance.study.instrument.name
        data['completed'] = administration_instance.completed
        data['due_date'] = administration_instance.due_date
        data['page_number'] = administration_instance.page_number
        data['hash_id'] = administration_instance.url_hash
        data['study_waiver'] = administration_instance.study.waiver
        raw_objects = []
        #meta_file['background_form'] = None

        for part in data['parts']:
            for item_type in part['types']:
                if 'sections' in item_type:
                    for section in item_type['sections']:
                        group_objects = instrument_model.objects.filter(category__exact=section['id']).values()
                        
                        x = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])
                        section['objects'] = x
                        raw_objects.extend(x)
                        if any(['*' in x['gloss'] for x in section['objects']]):
                            section['starred'] = "*Or the word used in your family"  

                                
                else:
                    group_objects = instrument_model.objects.filter(item_type__exact=item_type['id']).values()
                    x = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])
                    item_type['objects'] = x
                    raw_objects.extend(x)
        data['cdi_items'] = json.dumps(raw_objects, cls=DjangoJSONEncoder)
        try:
            age = BackgroundInfo.objects.filter(administration = administration_instance).values_list('age', flat=True)
        except:
            age = ''
        data['age'] = age                    
    return data


def parse_analysis(raw_answer):
    if raw_answer == 'True':
        answer = True
    elif raw_answer == 'False':
        answer = False
    else:
        answer = None
    return answer

def cdi_form(request, hash_id):

    administration_instance = get_administration_instance(hash_id)
    instrument_name = administration_instance.study.instrument.name
    instrument_model = model_map(instrument_name)
    refresh = False

    if request.method == 'POST' :
        if not administration_instance.completed and administration_instance.due_date > timezone.now():
            for key in request.POST:
                items = instrument_model.objects.filter(itemID = key)
                if len(items) == 1:
                    item = items[0]
                    value = request.POST[key]
                    if item.choices:
                        choices = map(unicode.strip, item.choices.split(';'))
                        if value in choices:
                            administration_data.objects.update_or_create(administration = administration_instance, item_ID = key, defaults = {'value': value})
                    else:
                        if value:
                            administration_data.objects.update_or_create(administration = administration_instance, item_ID = key, defaults = {'value': value})
            if 'btn-save' in request.POST and request.POST['btn-save'] == 'Save':
                try:
                    page_number = request.POST['page_number']
                    analysis = parse_analysis(request.POST['analysis'])
                    #analysis = request.POST['analysis']
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now(), page_number = page_number, analysis = analysis)
                except:
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                refresh = True
            elif 'btn-back' in request.POST and request.POST['btn-back'] == 'Go back to Background Info':
                administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                request.method = "GET"
                return background_info_form(request, hash_id)
            elif 'btn-submit' in request.POST and request.POST['btn-submit'] == 'Submit':
                try:
                    page_number = request.POST['page_number']
                    analysis = parse_analysis(request.POST['analysis'])
                    #analysis = request.POST['analysis']
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now(), analysis = analysis, completed= True)
                except:
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now(), completed= True)                
                return printable_view(request, hash_id)

    data = {}
    if request.method == 'GET' or refresh:
        data = prefilled_cdi_data(administration_instance)
        #with open(PROJECT_ROOT+'/form_data/English_WS_meta.json', 'r') as content_file:
        #    meta_file = json.loads(content_file.read())
        #    for part in meta_file['parts']:
        #        for item_type in part['types']:
        #            if 'sections' in item_type:
        #                for section in item_type['sections']:
        #                    section['objects'] = English_WS.objects.filter(category__exact=section['id']).values()
        #            else:
        #                item_type['objects'] = English_WS.objects.filter(item_type__exact=item_type['id']).values()
        #                if item_type['type'] == 'radiobutton':
        #                    for obj in item_type['objects']:
        #                        if obj['definition'].find('/') >=0:
        #                            obj['text'] = ''
        #                            obj['choices'] = obj['definition'].split('/')
        #                        else:
        #                            obj['text'] = obj['definition']
        #                            obj['choices'] = obj['choices'].split(';')
    return render(request, 'cdi_forms/cdi_form.html', data)

def printable_view(request, hash_id):
    administration_instance = get_administration_instance(hash_id)
    prefilled_data = {}
    if request.method == 'GET' or request.method=='POST':
        prefilled_data = prefilled_cdi_data(administration_instance)
        try:
            #Get form from database
            background_form = prefilled_background_form(administration_instance)
        except:
            #Blank form
            background_form = BackgroundForm()  
        prefilled_data['background_form'] = background_form
        prefilled_data['hash_id'] = hash_id
    
    return render(request, 'cdi_forms/printable_cdi.html', prefilled_data)


# def flat_prefilled_cdi_data(administration_instance):
#     prefilled_data_list = administration_data.objects.filter(administration = administration_instance).values('item_ID', 'value')
#     instrument_name = administration_instance.study.instrument.name
#     instrument_model = model_map(instrument_name)
#     prefilled_data = {x['item_ID']: x['value'] for x in prefilled_data_list}
#     with open(PROJECT_ROOT+'/form_data/'+instrument_name+'_meta.json', 'r') as content_file:
#         data = json.loads(content_file.read())
#         data['title'] = administration_instance.study.instrument.verbose_name
#         data['instrument_name'] = administration_instance.study.instrument.name
#         data['completed'] = administration_instance.completed
#         data['due_date'] = administration_instance.due_date
#         raw_objects = []

#         for part in data['parts']:
#             for item_type in part['types']:
#                 if 'sections' in item_type:
#                     for section in item_type['sections']:
#                         group_objects = instrument_model.objects.filter(category__exact=section['id']).values()
#                         x = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])
#                         raw_objects.extend(x)

                                
#                 else:
#                     group_objects = instrument_model.objects.filter(item_type__exact=item_type['id']).values()
#                     x = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])
#                     raw_objects.extend(x)
#         data['objects'] = json.dumps(raw_objects, cls=DjangoJSONEncoder)

                    
#     return data

# def graph_data(request, hash_id):
#     administration_instance = get_administration_instance(hash_id)
#     prefilled_data = {}
#     if request.method == 'GET' or request.method=='POST':
#         prefilled_data = flat_prefilled_cdi_data(administration_instance)
#         try:
#             age = BackgroundInfo.objects.filter(administration = administration_instance).values_list('age', flat=True)
#         except:
#             age = ''
#         prefilled_data['age'] = age
#         prefilled_data['hash_id'] = hash_id

#     return render(request, 'cdi_forms/graph.html', prefilled_data)


def administer_cdi_form(request, hash_id):
    try:
        administration_instance = administration.objects.get(url_hash = hash_id)
    except:
        raise Http404("Administration not found")

    refresh = False
    if request.method == 'POST':
        if not administration_instance.completed and administration_instance.due_date > timezone.now():
            requests_log.objects.create(url_hash = hash_id, request_type="POST")
            
            if 'background-info-form' in request.POST:
                return background_info_form(request, hash_id)

            elif 'cdi-form' in request.POST:
                return cdi_form(request, hash_id)

            else:
                refresh = True
        else:
            request.method = 'GET'

    if request.method == 'GET' or refresh:
        requests_log.objects.create(url_hash = hash_id, request_type="GET")
        if not administration_instance.completed and administration_instance.due_date > timezone.now():
            if administration_instance.completedBackgroundInfo:
                return cdi_form(request, hash_id)
            else:
                return background_info_form(request, hash_id)
        else:
            # only printable
            return printable_view(request, hash_id)

def find_paired_studies(request, study_group):
    possible_studies = study.objects.filter(study_group = study_group).values("name","instrument__min_age", "instrument__max_age", "instrument__language")
    data = {}
    data['background_form'] = BackgroundForm()
    data['possible_studies'] = json.dumps(list(possible_studies), cls=DjangoJSONEncoder)
    return render(request, 'cdi_forms/study_group.html', data)

def contact(request, hash_id):
    form = ContactForm(hash_id = hash_id)

    if request.method == 'POST':
        form = ContactForm(request.POST, hash_id = hash_id)

        if form.is_valid():
            contact_name = request.POST.get('contact_name', '')
            contact_email = request.POST.get('contact_email', '')
            contact_id = request.POST.get('contact_id', '')
            form_content = request.POST.get('content', '')
            template = get_template('cdi_forms/contact_template.txt')
            context = Context({
                'contact_name': contact_name,
                'contact_id': contact_id,
                'contact_email': contact_email,
                'form_content': form_content,
            })
            content = template.render(context)
            email = EmailMessage(
                "New contact form submission",
                content,
                "webcdi.stanford.edu" +'',
                ['dkellier@stanford.edu'],
                headers = {'Reply-To': contact_email }
            )
            email.send()
            messages.success(request, 'Form submission successful!')

    return render(request, 'cdi_forms/contact.html', {'form': form})    
