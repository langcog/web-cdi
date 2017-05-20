# -*- coding: utf-8 -*-

from django.shortcuts import render
from .models import English_WS, English_WG, BackgroundInfo, requests_log, Zipcode
import os.path, json, datetime, itertools, requests
from researcher_UI.models import administration_data, administration, study, payment_code, ip_address
from django.http import Http404
from .forms import BackgroundForm, ContactForm
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from ipware.ip import get_ip
from django.conf import settings



PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def model_map(name):
    mapping = {"English_WS": English_WS, "English_WG": English_WG}
    assert name in mapping, name+"instrument not added to the mapping in views.py model_map function"
    return mapping[name]
        
def get_model_header(name):
    return list(model_map(name).objects.values_list('itemID', flat=True))
    
def prefilled_background_form(administration_instance):
    background_instance = BackgroundInfo.objects.get(administration = administration_instance)

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
    age_ref['zip_code'] = ''
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

                if child_dob:
                    day_diff = datetime.date.today().day - child_dob.day
                    age = (datetime.date.today().year - child_dob.year) * 12 +  (datetime.date.today().month - child_dob.month) + (1 if day_diff >=15 else 0)
                else:
                    age = None
                if age:
                    background_instance.age = age

                zip_prefix = ''
                raw_zip = background_instance.zip_code
                if raw_zip and raw_zip != 'None':
                    zip_prefix = raw_zip[:3]
                    if Zipcode.objects.filter(zip_prefix = zip_prefix).exists():
                        zip_prefix = Zipcode.objects.filter(zip_prefix = zip_prefix).first().state
                    else:
                        zip_prefix = zip_prefix + '**'
                background_instance.zip_code = zip_prefix

                background_instance.administration = administration_instance
                background_instance.save()
                if 'btn-next' in request.POST and request.POST['btn-next'] == 'Next':
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
            if len(background_instance.zip_code) == 3:
                background_instance.zip_code = background_instance.zip_code + '**'
            background_form = BackgroundForm(instance = background_instance, age_ref = age_ref)
        except:
            #Blank form
            background_form = BackgroundForm(age_ref = age_ref)  
    data = {}
    data['background_form'] = background_form
    data['hash_id'] = hash_id
    data['username'] = administration_instance.study.researcher.username
    data['completed'] = administration_instance.completed
    data['due_date'] = administration_instance.due_date
    data['language'] = administration_instance.study.instrument.language
    data['title'] = administration_instance.study.instrument.verbose_name
    data['max_age'] = administration_instance.study.instrument.max_age
    data['min_age'] = administration_instance.study.instrument.min_age
    data['study_waiver'] = administration_instance.study.waiver
    data['allow_payment'] = administration_instance.study.allow_payment
    if data['allow_payment'] and administration_instance.bypass is None:
        try:
            data['gift_amount'] = payment_code.objects.filter(study = administration_instance.study).values_list('gift_amount', flat=True).first()
        except:
            data['gift_amount'] = None
    study_name = administration_instance.study.name
    study_group = administration_instance.study.study_group
    if study_group:
        data['study_group'] = study_group
        data['alt_study_info'] = study.objects.filter(study_group = study_group, researcher = administration_instance.study.researcher ).exclude(name = study_name).values_list("name","instrument__min_age", "instrument__max_age", "instrument__language")
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
        data['confirm_completion'] = administration_instance.study.confirm_completion
        raw_objects = []

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

                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now(), page_number = page_number, analysis = analysis)
                except:
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                refresh = True
            elif 'btn-back' in request.POST and request.POST['btn-back'] == 'Go back to Background Info':
                administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())
                request.method = "GET"
                return background_info_form(request, hash_id)
            elif 'btn-submit' in request.POST and request.POST['btn-submit'] == 'Submit':
                result = {'success': None}
                recaptcha_response = request.POST.get('g-recaptcha-response', None)
                if recaptcha_response:
                    dt = {
                        'secret': settings.RECAPTCHA_PRIVATE_KEY,
                        'response': recaptcha_response
                    }
                    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=dt)
                    result = r.json()

                if administration_instance.study.allow_payment and administration_instance.bypass is None:
                    if (administration_instance.study.confirm_completion and result['success']) or not administration_instance.study.confirm_completion:

                        given_code = payment_code.objects.filter(hash_id__isnull = True, study = administration_instance.study).first()

                        if given_code:
                            given_code.hash_id = hash_id
                            given_code.assignment_date = datetime.datetime.now()
                            given_code.save()

                if administration_instance.study.researcher.username == "langcoglab" and administration_instance.study.allow_payment:
                    user_ip = str(get_ip(request))
                    print user_ip

                    if user_ip and user_ip != 'None':
                        ip_address.objects.create(study = administration_instance.study,ip_address = user_ip)

                try:
                    page_number = request.POST['page_number']
                    analysis = parse_analysis(request.POST['analysis'])
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now(), analysis = analysis)
                except:
                    administration.objects.filter(url_hash = hash_id).update(last_modified = datetime.datetime.now())                
                administration.objects.filter(url_hash = hash_id).update(completed = True)
                return printable_view(request, hash_id)

    data = {}
    if request.method == 'GET' or refresh:
        data = prefilled_cdi_data(administration_instance)
        data['created_date'] = administration_instance.created_date
        data['captcha'] = None
        if administration_instance.study.confirm_completion and administration_instance.study.researcher.username == "langcoglab" and administration_instance.study.allow_payment:
            data['captcha'] = 'True'

    return render(request, 'cdi_forms/cdi_form.html', data)

def printable_view(request, hash_id):
    administration_instance = get_administration_instance(hash_id)
    completed = int(request.get_signed_cookie('completed_num', '0'))
    prefilled_data = {}

    prefilled_data = prefilled_cdi_data(administration_instance)
    try:
        #Get form from database
        background_form = prefilled_background_form(administration_instance)
    except:
        #Blank form
        background_form = BackgroundForm()  
    prefilled_data['background_form'] = background_form
    prefilled_data['hash_id'] = hash_id
    prefilled_data['gift_code'] = None
    prefilled_data['gift_amount'] = None
    if administration_instance.study.allow_payment and administration_instance.bypass is None:
        if payment_code.objects.filter(hash_id = hash_id).exists():
            gift_card = payment_code.objects.get(hash_id = hash_id)
            prefilled_data['gift_code'] = gift_card.gift_code
            prefilled_data['gift_amount'] = gift_card.gift_amount
        else:
            prefilled_data['gift_code'] = 'ran out'
            prefilled_data['gift_amount'] = 'ran out'

    prefilled_data['allow_sharing'] = administration_instance.study.allow_sharing
    response = render(request, 'cdi_forms/printable_cdi.html', prefilled_data)

    if administration_instance.study.researcher.username == "langcoglab" and administration_instance.study.allow_payment:
        response.set_signed_cookie('completed_num',str(completed))
    return response



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

def find_paired_studies(request, username, study_group):
    researcher = User.objects.get(username = username)
    possible_studies = study.objects.filter(study_group = study_group, researcher = researcher).values("name","instrument__min_age", "instrument__max_age", "instrument__language","subject_cap").annotate(admin_count=models.Sum(
    models.Case(
        models.When(administration__completed=True, then=1),
        default=0, output_field=models.IntegerField()
    ))).annotate(slots_left=models.F('subject_cap')-models.F('admin_count'))
    data = {}
    data['background_form'] = BackgroundForm()
    data['possible_studies'] = json.dumps(list(possible_studies), cls=DjangoJSONEncoder)
    data['username'] = username
    return render(request, 'cdi_forms/study_group.html', data)

def contact(request, hash_id):

    redirect_url = ''.join(['http://', get_current_site(request).domain, reverse('administer_cdi_form', args=[hash_id])])

    form = ContactForm(redirect_url = redirect_url)

    if request.method == 'POST':

        form = ContactForm(request.POST, redirect_url = redirect_url)

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
