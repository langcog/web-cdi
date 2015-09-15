from django.shortcuts import render

from django.http import HttpResponse

from .models import English_WS
import os.path
import json
from researcher_UI.models import administration_data, administration
from django.http import Http404
import datetime
from .forms import BackgroundForm


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def cdi_form(request):
    with open(PROJECT_ROOT+'/form_data/English_WS_meta.json', 'r') as content_file:
        meta_file = json.loads(content_file.read())
        for part in meta_file['parts']:
            for item_type in part['types']:
                if 'sections' in item_type:
                    for section in item_type['sections']:
                        section['objects'] = English_WS.objects.filter(category__exact=section['id']).values()
                else:
                    item_type['objects'] = English_WS.objects.filter(item_type__exact=item_type['id']).values()
                    if item_type['type'] == 'radiobutton':
                        for obj in item_type['objects']:
                            if obj['definition'].find('/') >=0:
                                obj['text'] = ''
                                obj['choices'] = obj['definition'].split('/')
                            else:
                                obj['text'] = obj['definition']
                                obj['choices'] = obj['choices'].split(';')
                    print item_type['objects']
    return render(request, 'cdi_forms/cdi.html', meta_file)
    
def administer_cdi_form(request, hash_id):
    try:
        administration_instance = administration.objects.get(url_hash = hash_id)
    except:
        raise Http404("Administration not found")

    background_form = BackgroundForm() if not request.method == 'POST' else BackgroundForm(request.POST)
        
        
    if request.method == 'POST' :
        if not administration_instance.completed:
            bulk_data = []
            for key in request.POST:
                items = English_WS.objects.filter(itemID = key)
                if len(items) == 1:
                    item = items[0]
                    choices = map(unicode.strip, item.choices.split(';'))
                    value = request.POST[key]
                    if value in choices:
                        administration_data.objects.update_or_create(administration = administration_instance, item_ID = key, value= value)
            if 'submit' in request.POST and request.POST['submit'] == 'Submit':
                administration.objects.filter(url_hash = hash_id).update(completed= True)

            if 'save' in request.POST and request.POST['save'] == 'Save':
                administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
        refresh = True


    if request.method == 'GET' or refresh:
        prefilled_data_list = administration_data.objects.filter(administration = administration_instance).values('item_ID', 'value')

        prefilled_data = {x['item_ID']:x['value'] for x in prefilled_data_list}
        
        

        with open(PROJECT_ROOT+'/form_data/English_WS_meta.json', 'r') as content_file:
            meta_file = json.loads(content_file.read())
            meta_file['completed'] = administration_instance.completed
            meta_file['due_date'] = administration_instance.due_date
            meta_file['background_form'] = background_form

            for part in meta_file['parts']:
                for item_type in part['types']:
                    if 'sections' in item_type:
                        for section in item_type['sections']:
                            section['objects'] = English_WS.objects.filter(category__exact=section['id']).values()
                            for obj in section['objects']:
                                obj['prefilled_value'] = obj['itemID'] in prefilled_data
                                    
                    else:
                        item_type['objects'] = English_WS.objects.filter(item_type__exact=item_type['id']).values()
                        if item_type['type'] == 'checkbox':
                            for obj in item_type['objects']:
                                obj['prefilled_value'] = obj['itemID'] in prefilled_data

                        if item_type['type'] == 'radiobutton':
                            for obj in item_type['objects']:
                                split_definition = map(unicode.strip, obj['definition'].split('/'))
                                split_choices = map(unicode.strip, obj['choices'].split(';'))
                                prefilled_values = [False if obj['itemID'] not in prefilled_data else x == prefilled_data[obj['itemID']] for x in split_choices]
                                if obj['definition'].find('/') >=0:
                                    obj['text'] = ''
                                    obj['choices'] = zip(split_definition, split_choices, prefilled_values)
                                else:
                                    obj['text'] = obj['definition']
                                    obj['choices'] = zip(split_choices, split_choices, prefilled_values)
                        print item_type['objects']
        return render(request, 'cdi_forms/cdi.html', meta_file)
