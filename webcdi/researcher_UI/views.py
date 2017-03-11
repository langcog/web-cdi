# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import AddStudyForm, RenameStudyForm, AddPairedStudyForm
from .models import study, administration, administration_data, get_meta_header, get_background_header
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




# Create your views here


class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8-sig", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
    def writerow(self, row):
        '''writerow(unicode) -> None
        This function takes a Unicode string and encodes it to the output.
        '''
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

@login_required
def download_data(request, study_obj, administrations = None):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_data.csv'''

    writer = UnicodeWriter(response)
    
    model_header = get_model_header(study_obj.instrument.name)
    
    meta_data_header = get_meta_header()
    background_header = get_background_header()
    writer.writerow(meta_data_header+background_header+model_header)
    for admin_obj in administrations:
        admin_data = {x:y for (x,y) in administration_data.objects.values_list('item_ID', 'value').filter(administration_id = admin_obj)}
        background_data = []
        modified_admin = admin_obj.get_meta_data()

        if 'VANITY_URL' in os.environ:
            modified_admin[3] = os.environ['VANITY_URL'] + "/form/fill/" + modified_admin[3]
        else:
            modified_admin[3] = request.get_host() + "/form/fill/" + modified_admin[3]

        for i in background_header:
            try:
                raw_background_value = BackgroundInfo.objects.values_list(i, flat=True).filter(administration = admin_obj)
                try:
                    background_value = dict(BackgroundInfo._meta.get_field(i).choices).get(raw_background_value[0])
                    if background_value:
                        background_data.append(force_text(background_value))
                    else:
                        background_data.append(force_text(raw_background_value[0]))
                except:
                    background_data.append(force_text(raw_background_value[0]))
            except:
                background_data.append("")
    	writer.writerow([force_text(s) for s in modified_admin]+background_data+[force_text(admin_data[key]) if key in admin_data else '' for key in model_header])
    print response
    return response


@login_required
def download_dictionary(request, study_obj):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.instrument.name+'_dictionary.csv'''
    writer = UnicodeWriter(response)

    item_properties = ['itemID','item_type','category','definition','gloss']
    writer.writerow(item_properties)

    raw_item_data = model_map(study_obj.instrument.name).objects.values_list('itemID','item_type','category','definition','gloss')
    item_data = [list(elem) for elem in raw_item_data]

    for item in item_data:
        writer.writerow([force_text(s) for s in item])
    return response    

@login_required
def download_links(request, study_obj, administrations = None):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_links.csv'''

    writer = UnicodeWriter(response)

    meta_data_header = get_meta_header()[0:4]
    writer.writerow(meta_data_header)

    for admin_obj in administrations:
        modified_admin = admin_obj.get_meta_data()[0:4]

        if 'VANITY_URL' in os.environ:
            modified_admin[3] = os.environ['VANITY_URL'] + "/form/fill/" + modified_admin[3]
        else:
            modified_admin[3] = request.get_host() + "/form/fill/" + modified_admin[3]

        writer.writerow([force_text(s) for s in modified_admin])
    print response
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
                        administrations = list(administration.objects.filter(id__in = ids))
                        return download_links(request, study_obj, administrations)
                        refresh = True


                elif 'download-selected' in request.POST:
                    ids = request.POST.getlist('select_col')
                    #header = get_cdi_model['English_WS'].
                    if all([x.isdigit() for x in ids]):
                        ids = list(set(map(int, ids)))
                        administrations = []
                        for nid in ids:
                            administrations.append(administration.objects.get(id = nid))
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
        context['studies'] = study.objects.filter(researcher = request.user)
        context['instruments'] = []
        if study_name is not None:
            current_study = study.objects.get(researcher= request.user, name= study_name)
            administration_table = StudyAdministrationTable(administration.objects.filter(study = current_study))
            RequestConfig(request, paginate={'per_page': num_per_page}).configure(administration_table)
            context['current_study'] = current_study.name
            context['num_per_page'] = num_per_page
            context['study_instrument'] = current_study.instrument.verbose_name
            context['study_group'] = current_study.study_group
            context['study_administrations'] = administration_table
        return render(request, 'researcher_UI/interface.html', context)

@login_required 
def rename_study(request, study_name):
    data = {}
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)
    if request.method == 'POST' :
        form = RenameStudyForm(study_name, request.POST)
        if form.is_valid():
            researcher = request.user
            new_study_name = form.cleaned_data.get('name')
            new_study_waiver = form.cleaned_data.get('waiver')
            if not study.objects.filter(researcher = researcher, name = new_study_name).exists():
    	        study_obj.name = new_study_name
                study_obj.waiver = new_study_waiver
                study_obj.save()
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+new_study_name+"/";
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data['stat'] = "error";
                data['error_message'] = "Study already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "re-render";
            return render(request, 'researcher_UI/add_study_modal.html', {'form': form})
    else:
        form = RenameStudyForm(study_name)
        return render(request, 'researcher_UI/add_study_modal.html', {'form': form})
@login_required 
def add_study(request):
    data = {}
    if request.method == 'POST' :
        form = AddStudyForm(request.POST)
        if form.is_valid():
            researcher = request.user
            study_name = form.cleaned_data.get('name')
            instrument = form.cleaned_data.get('instrument')
            waiver = form.cleaned_data.get('waiver')
            if not study.objects.filter(researcher = researcher, name = study_name).exists():
                new_study = study(researcher = researcher, name = study_name, instrument = instrument, waiver = waiver)
                new_study.save()
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+study_name+"/";
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                data['stat'] = "error";
                data['error_message'] = "Study already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data['stat'] = "re-render";
            return render(request, 'researcher_UI/add_study_modal.html', {'form': form})
    else:
        form = AddStudyForm()
        return render(request, 'researcher_UI/add_study_modal.html', {'form': form})

@login_required 
def add_paired_study(request):
    data = {}
    if request.method == 'POST' :
        form = AddPairedStudyForm(request.POST)
        if form.is_valid():
            researcher = request.user
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
        form = AddPairedStudyForm()
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
            ids_csv = request.FILES['subject-ids-csv'] if 'subject-ids-csv' in request.FILES else None
            print ids_csv

            if params['new-subject-ids'][0] == '' and params['autogenerate-count'][0] == '' and ids_csv is None:
                validity = False
                data['error_message'] += "Form is empty\n"

            if ids_csv:
                ids_to_add = iter(csv.reader(ids_csv, delimiter=','))
                if 'ignore-csv-header' in request.POST:
                    next(ids_to_add)
                subject_ids_numbers = all([x[0].isdigit() for x in ids_to_add])
                if not subject_ids_numbers:
                    validity = False
                    if 'ignore-csv-header' not in request.POST:
                        data['error_message'] += "Non integer subject ids. Make sure first row is numeric\n"
                    else:
                        data['error_message'] += "Non integer subject ids\n"


            if params['new-subject-ids'][0] != '':
                subject_ids = re.split('[,\s]+', str(params['new-subject-ids'][0]))
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

                if ids_csv:
                    ids_to_add = iter(csv.reader(ids_csv, delimiter=','))
                    if 'ignore-csv-header' in request.POST:
                        next(ids_to_add)
                    subject_ids = [x[0] for x in ids_to_add]
                    for sid in subject_ids:
                        new_hash = random_url_generator()
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now()+ datetime.timedelta(days=14)))

                if params['new-subject-ids'][0] != '':
                    subject_ids = re.split('[,\s]+', str(params['new-subject-ids'][0]))
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
#
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
        return render(request, 'researcher_UI/administer_new_modal.html', {'study_name': study_name})

def administer_new_parent(request, study_name):
    data={}
    new_administrations = []
    autogenerate_count = 1
    study_obj = study.objects.get(name= study_name)
    max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max']
    if max_subject_id is None:
        max_subject_id = 0
    for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1):
        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14)))


    new_url = new_administrations[0]
    new_hash_id = new_url.url_hash
    administration.objects.bulk_create(new_administrations)
    redirect_url = "/form/fill/"+new_hash_id+"/"
    background_info_form(request, new_hash_id)
    return redirect(redirect_url)


