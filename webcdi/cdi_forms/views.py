from django.shortcuts import render

from django.http import HttpResponse

from .models import English_WS
import os.path
import json


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
