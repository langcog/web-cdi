# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import AddStudyForm, RenameStudyForm, AddPairedStudyForm
from .models import study, administration, administration_data, get_meta_header, get_background_header, payment_code
import codecs, json
import os
import re, random
from .tables  import StudyAdministrationTable
from django_tables2   import RequestConfig
from django.db.models import Max
import datetime
from cdi_forms.views import model_map, get_model_header, background_info_form, prefilled_background_form
from cdi_forms.models import BackgroundInfo
import cStringIO
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
import csv
from django.contrib.auth.models import User
import pandas as pd
from django.core.urlresolvers import reverse
from decimal import Decimal






# Create your views here


@login_required
def download_data(request, study_obj, administrations = None):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_data.csv'''
    
    model_header = get_model_header(study_obj.instrument.name)
    admin_header = ['study_name', 'subject_id','repeat_num', 'administration_id', 'link', 'completed', 'completedBackgroundInfo', 'due_date', 'last_modified','created_date']
    
    # background_header = get_background_header()
    # writer.writerow(meta_data_header+background_header+model_header)

    answers = administration_data.objects.values('administration_id', 'item_ID', 'value').filter(administration_id__in = administrations)

    melted_answers = pd.DataFrame.from_records(answers).pivot(index='administration_id', columns='item_ID', values='value')
    melted_answers.reset_index(level=0, inplace=True)
    
    background_data = BackgroundInfo.objects.values().filter(administration__in = administrations)
    new_background = pd.DataFrame.from_records(background_data)

    for c in new_background.columns:
        try:
            new_background = new_background.replace({c: dict(BackgroundInfo._meta.get_field(c).choices)})
            # new_background[c] = new_background[c].map(dict(BackgroundInfo._meta.get_field(c).choices))
        except:
            pass

    background_answers = pd.merge(new_background, melted_answers, how='outer', on = 'administration_id')

    admin_data = pd.DataFrame.from_records(administrations.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'})
    admin_data['study_name'] = study_obj.name

    combined_data = pd.merge(admin_data, background_answers, how='outer', on = 'administration_id')
    test_url = request.build_absolute_uri(reverse('administer_cdi_form', args=['a'*64])).replace('a'*64+'/','')
    combined_data['link'] = test_url + combined_data['link']
    
    combined_data = combined_data[admin_header + [col for col in new_background.columns if col != 'administration_id'] + model_header ]

    combined_data.to_csv(response, encoding='utf-8')

    return response



@login_required
def download_dictionary(request, study_obj):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.instrument.name+'_dictionary.csv'''

    raw_item_data = model_map(study_obj.instrument.name).objects.values('itemID','item_type','category','definition','gloss')
    pd.DataFrame.from_records(raw_item_data).to_csv(response, encoding='utf-8')

    return response    

@login_required
def download_links(request, study_obj, administrations = None):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_links.csv'''

    admin_data = pd.DataFrame.from_records(administrations.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'})
    admin_data = admin_data[['study_name','subject_id', 'repeat_num', 'administration_id','link']]

    admin_data['study_name'] = study_obj.name

    test_url = request.build_absolute_uri(reverse('administer_cdi_form', args=['a'*64])).replace('a'*64+'/','')
    admin_data['link'] = test_url + admin_data['link']

    admin_data.to_csv(response, encoding='utf-8')


    return response

 
    

@login_required
def console(request, study_name = None, num_per_page = 20):
    refresh = False
    if request.method == 'POST' :
        data = {}
        permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
        study_obj = study.objects.get(researcher= request.user, name= study_name)
        if permitted :
            if request.method == 'POST' :
                ids = request.POST.getlist('select_col')
                if 'administer-selected' in request.POST:
                    if all([x.isdigit() for x in ids]):
                        num_ids = map(int, ids)
                        new_administrations = []
                        sids_created = set()
                        for nid in num_ids:
                            admin_instance = administration.objects.get(id = nid)
                            sid = admin_instance.subject_id
                            if sid in sids_created:
                                continue
                            old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                            new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14)))
                            sids_created.add(sid)


                        administration.objects.bulk_create(new_administrations)
                        refresh = True

                elif 'delete-selected' in request.POST:
                    ids = request.POST.getlist('select_col')
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        for nid in ids:
                            admin_object = administration.objects.get(id = nid)
                            admin_object.delete()
                        refresh = True

                elif 'download-links' in request.POST:
                    ids = request.POST.getlist('select_col')
                    administrations = []
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        administrations = administration.objects.filter(id__in = ids)
                        return download_links(request, study_obj, administrations)
                        refresh = True


                elif 'download-selected' in request.POST:
                    ids = request.POST.getlist('select_col')
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        administrations = administration.objects.filter(id__in = ids)
                        return download_data(request, study_obj, administrations)

                        refresh = True

                elif 'delete-study' in request.POST:
                    study_obj.delete()
                    study_name = None
                    refresh = True

                elif 'download-study' in request.POST:
                    administrations = administration.objects.filter(study = study_obj)
                    return download_data(request, study_obj, administrations)

                elif 'download-dictionary' in request.POST:
                    return download_dictionary(request, study_obj)

                elif 'view_all' in request.POST:
                    if request.POST['view_all'] == "Show All":
                        num_per_page = administration.objects.filter(study = study_obj).count()
                    elif request.POST['view_all'] == "Show 20":
                        num_per_page = 20
                    refresh = True

        
    if request.method == 'GET' or refresh:
        username = None
        if request.user.is_authenticated():
            username = request.user.username
        context = dict()
        context['username'] =  username 
        context['studies'] = study.objects.filter(researcher = request.user).order_by('id')
        context['instruments'] = []
        if study_name is not None:
            try:
                current_study = study.objects.get(researcher= request.user, name= study_name)
                administration_table = StudyAdministrationTable(administration.objects.filter(study = current_study))
                if not current_study.confirm_completion:
                    administration_table.exclude = ("study",'id', 'url_hash','completedBackgroundInfo', 'analysis')
                RequestConfig(request, paginate={'per_page': num_per_page}).configure(administration_table)
                context['current_study'] = current_study.name
                context['num_per_page'] = num_per_page
                context['study_instrument'] = current_study.instrument.verbose_name
                context['study_group'] = current_study.study_group
                context['study_administrations'] = administration_table
                context['completed_admins'] = administration.objects.filter(study = current_study, completed = True).count()
                context['unique_children'] = count = administration.objects.filter(study = current_study, completed = True).values('subject_id').distinct().count()
                context['allow_payment'] = current_study.allow_payment
                context['available_giftcards'] = payment_code.objects.filter(hash_id__isnull = True, study = current_study).count()
                print payment_code.objects
            except:
                pass
        return render(request, 'researcher_UI/interface.html', context)

@login_required 
def rename_study(request, study_name):
    data = {}
    form_package = {}
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)
    if request.method == 'POST' :
        form = RenameStudyForm(study_name, request.POST)
        changed_name = None
        changed_waiver = None
        raw_gift_codes = None
        all_new_codes = None
        old_codes = None
        amount_regex = None
        if form.is_valid():
            researcher = request.user
            new_study_name = form.cleaned_data.get('name')
            waiver = form.cleaned_data.get('waiver')
            raw_gift_codes = form.cleaned_data.get('gift_codes')
            raw_gift_amount = form.cleaned_data.get('gift_amount')
            print raw_gift_amount

            if not study.objects.filter(researcher = researcher, name = new_study_name).exists():
    	        study_obj.name = new_study_name
                changed_name = True
                study_obj.save()

            if study_obj.waiver != waiver:
                study_obj.waiver = waiver
                study_obj.save()
                changed_waiver = True

            if raw_gift_codes:
                new_payment_codes = []
                used_codes = []
                gift_codes = re.split('[,;\s\t\n]+', raw_gift_codes)
                gift_regex = re.compile(r'^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{4}$')
                gift_type = "Amazon"
                gift_codes = filter(gift_regex.search, gift_codes)                

                try:
                    amount_regex = Decimal(re.search('([0-9]{1,3})?.[0-9]{2}', raw_gift_amount).group(0))
                except:
                    pass

                if amount_regex:

                    for gift_code in gift_codes:
                        if not payment_code.objects.filter(payment_type = gift_type, gift_code = gift_code).exists():
                            new_payment_codes.append(payment_code(study =study_obj, payment_type = gift_type, gift_code = gift_code, gift_amount = amount_regex))
                        else:
                            used_codes.append(gift_code)
                if not used_codes:
                    all_new_codes = True


            if any([changed_name, changed_waiver, raw_gift_codes]):
                if raw_gift_codes:
                    if not all_new_codes or not amount_regex: 
                        data['stat'] = "error";
                        err_msg = []
                        if not all_new_codes:
                            err_msg = err_msg + ['The following codes are already in the database:'] + used_codes;
                        if not amount_regex:
                            err_msg = err_msg + [ "Please enter in a valid amount for \"Amount per Card\""];

                        print err_msg
                        data['error_message'] = "<br>".join(err_msg);
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        if all_new_codes:
                            payment_code.objects.bulk_create(new_payment_codes)
                            data['stat'] = "ok";
                            data['redirect_url'] = "/interface/study/"+new_study_name+"/";
                            return HttpResponse(json.dumps(data), content_type="application/json") 
                else:
                    data['stat'] = "ok";
                    data['redirect_url'] = "/interface/study/"+new_study_name+"/";
                    return HttpResponse(json.dumps(data), content_type="application/json")            
            else:

                data['stat'] = "error";
                data['error_message'] = "Study already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "re-render";
            form_package['form'] = form
            form_package['form_name'] = 'Update Study'
            form_package['allow_payment'] = study_obj.allow_payment
            return render(request, 'researcher_UI/add_study_modal.html', form_package)
    else:
        form = RenameStudyForm(study_name, study_waiver = study_obj.waiver)
        form_package['form'] = form
        form_package['form_name'] = 'Update Study'
        form_package['allow_payment'] = study_obj.allow_payment
        return render(request, 'researcher_UI/add_study_modal.html', form_package)
        
@login_required 
def add_study(request):
    data = {}
    if request.method == 'POST' :
        form = AddStudyForm(request.POST)
        if form.is_valid():
            study_instance = form.save(commit=False)
            researcher = request.user
            study_name = form.cleaned_data.get('name')
            study_instance.researcher = researcher


            # study_name = form.cleaned_data.get('name')
            # instrument = form.cleaned_data.get('instrument')
            # subject_cap = form.cleaned_data.get('subject_cap')
            # waiver = form.cleaned_data.get('waiver')
            # confirm_completion = form.cleaned_data.get('confirm_completion')
            if not study.objects.filter(researcher = researcher, name = study_name).exists():
                # new_study = study(researcher = researcher, name = study_name, instrument = instrument, waiver = waiver, confirm_completion = confirm_completion, subject_cap = subject_cap)
                # new_study.save()
                study_instance.save()
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+study_name+"/";
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data['stat'] = "error";
                data['error_message'] = "Study already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "re-render";
            return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})
    else:
        form = AddStudyForm()
        return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})

@login_required 
def add_paired_study(request):
    data = {}
    researcher = request.user
    if request.method == 'POST' :
        form = AddPairedStudyForm(request.POST)
        if form.is_valid():
            study_group = form.cleaned_data.get('study_group')
            paired_studies = form.cleaned_data.get('paired_studies')
            permissions = []
            for one_study in paired_studies:
                permitted = study.objects.filter(researcher = researcher,  name = one_study).exists()
                permissions.append(permitted)
                if permitted:
                    study_obj = study.objects.get(researcher = researcher,  name = one_study)                    
                    study_obj.study_group = study_group
                    study_obj.save()

            if all(True for permission in permissions):
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/";
                return HttpResponse(json.dumps(data), content_type="application/json")

            else:
                data['stat'] = "error";
                data['error_message'] = "Study group already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "re-render";
            return render(request, 'researcher_UI/add_paired_study_modal.html', {'form': form})
    else:
        your_studies = study.objects.filter(study_group = "", researcher = researcher).values_list("name","name")
        form = AddPairedStudyForm(your_studies = your_studies)
        return render(request, 'researcher_UI/add_paired_study_modal.html', {'form': form})

def random_url_generator(size=64, chars='0123456789abcdef'):
    return ''.join(random.choice(chars) for _ in range(size))


@login_required 
def administer_new(request, study_name):
    data = {}
    context = dict()
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)

    if request.method == 'POST' :
        if permitted :
            params = dict(request.POST)
            validity = True
            data['error_message'] = ''
            raw_ids_csv = request.FILES['subject-ids-csv'] if 'subject-ids-csv' in request.FILES else None

            if params['new-subject-ids'][0] == '' and params['autogenerate-count'][0] == '' and raw_ids_csv is None:
                validity = False
                data['error_message'] += "Form is empty\n"

            if raw_ids_csv:
                if 'csv-header' in request.POST:
                    ids_df = pd.read_csv(raw_ids_csv)
                    if request.POST['subject-ids-column']:
                        subj_column = request.POST['subject-ids-column']
                        if subj_column in ids_df.columns:
                            ids_to_add = ids_df[subj_column]
                            ids_type =  ids_to_add.dtype
                        else:
                            ids_type = 'missing'

                    else:
                        ids_to_add = ids_df[ids_df.columns[0]]
                        ids_type =  ids_to_add.dtype

                else:
                    ids_df = pd.read_csv(raw_ids_csv, header = None)
                    ids_to_add = ids_df[ids_df.columns[0]]
                    ids_type =  ids_to_add.dtype

                if ids_type != 'int64':
                    validity = False
                    if 'csv-header' not in request.POST:
                        data['error_message'] += "Non integer subject ids. Make sure first row is numeric\n"
                    else:
                        if ids_type == 'missing':
                            data['error_message'] += "Unable to find specified column. Check for any typos."
                        else:
                            data['error_message'] += "Non integer subject ids\n"


            if params['new-subject-ids'][0] != '':
                subject_ids = re.split('[,;\s\t\n]+', str(params['new-subject-ids'][0]))
                subject_ids = filter(None, subject_ids)
                subject_ids_numbers = all([x.isdigit() for x in subject_ids])
                if not subject_ids_numbers:
                    validity = False
                    data['error_message'] += "Non integer subject ids\n"

            if params['autogenerate-count'][0] != '':
                autogenerate_count = params['autogenerate-count'][0]
                autogenerate_count_isdigit = autogenerate_count.isdigit()
                if not autogenerate_count_isdigit:
                    validity = False
                    data['error_message'] += "Non integer number of IDs to autogenerate\n"

            if validity:
                new_administrations = []

                if raw_ids_csv:

                    subject_ids = ids_to_add.tolist()
                    print subject_ids

                    for sid in subject_ids:
                        new_hash = random_url_generator()
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+ datetime.timedelta(days=14)))

                if params['new-subject-ids'][0] != '':
                    subject_ids = re.split('[,;\s\t\n]+', str(params['new-subject-ids'][0]))
                    subject_ids = filter(None, subject_ids)
                    subject_ids = map(int, subject_ids)
                    for sid in subject_ids:
                        new_hash = random_url_generator()
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+ datetime.timedelta(days=14)))


                if params['autogenerate-count'][0]!='':
                    autogenerate_count = int(params['autogenerate-count'][0])
                    max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max']
                    if max_subject_id is None:
                        max_subject_id = 0
                    for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1):
                        new_hash = random_url_generator()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14)))

                administration.objects.bulk_create(new_administrations)
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+study_name+"/?sort=-created_date";
                data['study_name'] = study_name
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data['stat'] = "error";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "error";
            data['error_message'] = "permission denied";
            data['redirect_url'] = "interface/";
            return HttpResponse(json.dumps(data), content_type="application/json")
    else:
        context['username'] = request.user.username
        context['study_name'] = study_name
        context['study_group'] = study_obj.study_group
        return render(request, 'researcher_UI/administer_new_modal.html', context)

def administer_new_parent(request, username, study_name):
    data={}
    new_administrations = []
    autogenerate_count = 1
    researcher = User.objects.get(username = username)
    study_obj = study.objects.get(name= study_name, researcher = researcher)
    subject_cap = study_obj.subject_cap
    completed_admins = administration.objects.filter(study = study_obj, completed = True).count()
    bypass = request.GET.get('bypass', None)

    if completed_admins < subject_cap:
        let_through = True
    elif subject_cap is None:
        let_through = True
    elif bypass:
        let_through = True
    else:
        let_through = None

    if let_through:
        max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max']
        if max_subject_id is None:
            max_subject_id = 0
        for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1):
            new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14)))

        new_url = new_administrations[0]
        new_hash_id = new_url.url_hash
        administration.objects.bulk_create(new_administrations)
        redirect_url = reverse('administer_cdi_form', args=[new_url.url_hash])
        background_info_form(request, new_hash_id)
    else:
        redirect_url = reverse('overflow', args=[username, study_name])
    return redirect(redirect_url)

def overflow(request, username, study_name):
    data = {}
    data['username'] = username
    data['study_name'] = study_name
    return render(request, 'cdi_forms/overflow.html', data)

