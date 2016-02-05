from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import AddStudyForm, RenameStudyForm
from .models import study, administration, administration_data, get_meta_header 
import json
import re, random
from .tables  import StudyAdministrationTable
from django_tables2   import RequestConfig
from django.db.models import Max
import datetime
from cdi_forms.views import get_model_header

# Create your views here

import csv
from django.http import HttpResponse

@login_required
def download_data(request, study_obj, administrations = None):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name.replace(' ', '_')+'"-data.csv"'

    writer = csv.writer(response)
    

    #if(len(administrations) == 0):
        #return None;
    model_header = get_model_header(study_obj.instrument.name)
    
    meta_data_header = get_meta_header()
    writer.writerow(meta_data_header+model_header)
    for admin_obj in administrations:
        admin_data = {x:y for (x,y) in administration_data.objects.values_list('item_ID', 'value').filter(administration_id = admin_obj)}
	
    	writer.writerow(admin_obj.get_meta_data()+[admin_data[key] if key in admin_data else '' for key in model_header])
    return response

@login_required
def console(request, study_name = None):
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
            RequestConfig(request).configure(administration_table)
            context['current_study'] = current_study.name
            context['study_instrument'] = current_study.instrument.verbose_name
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
            if not study.objects.filter(researcher = researcher, name = new_study_name).exists():
	        study_obj.name = new_study_name
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
            if not study.objects.filter(researcher = researcher, name = study_name).exists():
                new_study = study(researcher = researcher, name = study_name, instrument = instrument)
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

def random_url_generator(size=64, chars='0123456789abcdef'):
    return ''.join(random.choice(chars) for _ in range(size))

@login_required 
def download_study(request, study_name):
    data = {}
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)



    


@login_required 
def administer_new(request, study_name):
    data = {}
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)

    if request.method == 'POST' :
        if permitted :
            params = dict(request.POST)
            validity = True
            data['error_message'] = ''
            if params['new-subject-ids'][0] == '' and params['autogenerate-count'][0] == '':
                validity = False
                data['error_message'] += "Form is empty\n"

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
                if params['new-subject-ids'][0] != '':
                    subject_ids = re.split('[,\s]+', str(params['new-subject-ids'][0]))
                    subject_ids = filter(None, subject_ids)
                    subject_ids = map(int, subject_ids)
                    for sid in subject_ids:
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+ datetime.timedelta(days=14)))


                if params['autogenerate-count'][0]!='':
                    autogenerate_count = int(params['autogenerate-count'][0])
                    max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max']
                    if max_subject_id is None:
                        max_subject_id = 0
                    for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1):
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14)))
#
                administration.objects.bulk_create(new_administrations)
                data['stat'] = "ok";
                data['redirect_url'] = "/interface/study/"+study_name+"/";
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
        return render(request, 'researcher_UI/administer_new_modal.html')

