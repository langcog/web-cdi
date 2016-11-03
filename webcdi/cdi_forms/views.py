from django.shortcuts import render
from .models import English_WS, English_WG, BackgroundInfo, requests_log
import os.path
import json
from researcher_UI.models import administration_data, administration
from django.http import Http404
import datetime
from .forms import BackgroundForm
from django.utils import timezone
from django.http import JsonResponse


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
    refresh = False
    background_form = None
        
    if request.method == 'POST' :
        if not administration_instance.completed and administration_instance.due_date > timezone.now():
            try:
                background_instance = BackgroundInfo.objects.get(administration = administration_instance)
                background_form = BackgroundForm(request.POST, instance = background_instance)
            except:
                background_form = BackgroundForm(request.POST)

            if background_form.is_valid():
                background_instance = background_form.save(commit = False)
                child_dob = background_form.cleaned_data.get('child_dob')
                #age = (datetime.date.today() - background_form.cleaned_data.get('child_dob'))
                #age = age.year*12 + age.month + (age.day >= 15)
                age = (datetime.date.today().year - child_dob.year) * 12 +  (datetime.date.today().month - child_dob.month) + (child_dob.day >=15)
                #validity of age is checked in the modelform's clean method
                background_instance.age = age
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
            background_form = prefilled_background_form(administration_instance)
        except:
            #Blank form
            background_form = BackgroundForm()  
    data = {}
    data['background_form'] = background_form
    data['completed'] = administration_instance.completed
    data['due_date'] = administration_instance.due_date
    data['title'] = administration_instance.study.instrument.verbose_name
    return render(request, 'cdi_forms/background_info.html', data)

def cdi_items(object_group, item_type, prefilled_data, item_id):
    for obj in object_group:
        if item_type == 'checkbox':
            obj['prefilled_value'] = obj['itemID'] in prefilled_data
            if obj['gloss'] is None:
                obj['gloss'] = obj['definition']

        if item_type == 'radiobutton':
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
                print obj['prefilled_value']

    return object_group 


def prefilled_cdi_data(administration_instance):
    prefilled_data_list = administration_data.objects.filter(administration = administration_instance).values('item_ID', 'value')
    instrument_name = administration_instance.study.instrument.name
    instrument_model = model_map(instrument_name)
    prefilled_data = {x['item_ID']: x['value'] for x in prefilled_data_list}
    with open(PROJECT_ROOT+'/form_data/'+instrument_name+'_meta.json', 'r') as content_file:
        data = json.loads(content_file.read())
        data['title'] = administration_instance.study.instrument.verbose_name
        data['completed'] = administration_instance.completed
        data['due_date'] = administration_instance.due_date
        #meta_file['background_form'] = None

        for part in data['parts']:
            for item_type in part['types']:
                if 'sections' in item_type:
                    for section in item_type['sections']:
                        group_objects = instrument_model.objects.filter(category__exact=section['id']).values()
               
                        section['objects'] = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])
                        if any(['*' in x['gloss'] for x in section['objects']]):
                            section['starred'] = "*Or the word used in your family"  

                                
                else:
                    group_objects = instrument_model.objects.filter(item_type__exact=item_type['id']).values()
                    item_type['objects'] = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])

                    
    return data

def cdi_response_data(administration_instance):
    prefilled_data_list = administration_data.objects.filter(administration = administration_instance).values('item_ID', 'value')
    instrument_name = administration_instance.study.instrument.name
    instrument_model = model_map(instrument_name)
    prefilled_data = {x['item_ID']: x['value'] for x in prefilled_data_list}
    with open(PROJECT_ROOT+'/form_data/'+instrument_name+'_meta.json', 'r') as content_file:
        data = json.loads(content_file.read())
        data['title'] = administration_instance.study.instrument.verbose_name
        #data['completed'] = administration_instance.completed
        #data['due_date'] = administration_instance.due_date
        #meta_file['background_form'] = None

        for part in data['parts']:
            for item_type in part['types']:
                if 'sections' in item_type:
                    for section in item_type['sections']:
                        group_objects = instrument_model.objects.filter(category__exact=section['id']).values()
               
                        section['objects'] = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])
                        if any(['*' in x['gloss'] for x in section['objects']]):
                            section['starred'] = "*Or the word used in your family"  

                                
                else:
                    group_objects = instrument_model.objects.filter(item_type__exact=item_type['id']).values()
                    item_type['objects'] = cdi_items(group_objects, item_type['type'], prefilled_data, item_type['id'])

    return data

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
                            administration_data.objects.update_or_create(administration = administration_instance, item_ID = key, value = value)
                    else:
                        if value:
                            administration_data.objects.update_or_create(administration = administration_instance, item_ID = key, value = value)
            if 'btn-save' in request.POST and request.POST['btn-save'] == 'Save':
                administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                refresh = True
            elif 'btn-back' in request.POST and request.POST['btn-back'] == 'Back':
                administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                request.method = "GET"
                return background_info_form(request, hash_id)
            elif 'btn-submit' in request.POST and request.POST['btn-submit'] == 'Submit':
                administration.objects.filter(url_hash = hash_id).update(completed= True)
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
    
    return render(request, 'cdi_forms/printable_cdi.html', prefilled_data)

def visualize_cdi_result(request, hash_id):   
    return render(request, 'cdi_forms/graph.html', {'hash_id': hash_id})

# def words(request, hash_id):
#     administration_instance = get_administration_instance(hash_id)
    
#     return JsonResponse({'hash_id': hash_id})

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
