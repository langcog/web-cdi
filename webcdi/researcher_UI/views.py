# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import *
from .models import researcher, study, administration, administration_data, get_meta_header, get_background_header, payment_code, ip_address
import codecs, json, os, re, random, csv, datetime, cStringIO, math, StringIO, zipfile
from .tables  import StudyAdministrationTable
from django_tables2   import RequestConfig
from django.db.models import Max
from cdi_forms.views import model_map, get_model_header, background_info_form, prefilled_background_form
from cdi_forms.models import BackgroundInfo, Zipcode
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
import pandas as pd
import numpy as np
import requests
from django.urls import reverse
from decimal import Decimal
from django.contrib.sites.shortcuts import get_current_site
from ipware.ip import get_ip
from psycopg2.extras import NumericRange
from django.conf import settings
from django.utils import timezone




@login_required # For researchers only, requires user to be logged in (test-takers do not have an account and are blocked from this interface)
def download_data(request, study_obj, administrations = None): # Download study data
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv') # Format response as a CSV
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_data.csv''' # Name the CSV response
    
    administrations = administrations if administrations is not None else administration.objects.filter(study = study_obj)
    model_header = get_model_header(study_obj.instrument.name) # Fetch the associated instrument model's variables
    
    # Fetch administration variables
    admin_header = ['study_name', 'subject_id','repeat_num', 'administration_id', 'link', 'completed', 'completedBackgroundInfo', 'due_date', 'last_modified','created_date']

    # Fetch background data variables
    background_header = ['age','sex','zip_code','birth_order', 'birth_weight_lb', 'birth_weight_kg','multi_birth_boolean','multi_birth', 'born_on_due_date', 'early_or_late', 'due_date_diff', 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income', 'child_hispanic_latino', 'child_ethnicity', 'caregiver_info', 'other_languages_boolean','other_languages','language_from', 'language_days_per_week', 'language_hours_per_day', 'ear_infections_boolean','ear_infections', 'hearing_loss_boolean','hearing_loss', 'vision_problems_boolean','vision_problems', 'illnesses_boolean','illnesses', 'services_boolean','services','worried_boolean','worried','learning_disability_boolean','learning_disability']

    # Try to properly format CDI responses for pandas dataframe
    try:
        answers = administration_data.objects.values('administration_id', 'item_ID', 'value').filter(administration_id__in = administrations)
        melted_answers = pd.DataFrame.from_records(answers).pivot(index='administration_id', columns='item_ID', values='value')
        melted_answers.reset_index(level=0, inplace=True)
    except:
        melted_answers = pd.DataFrame(columns = get_model_header(study_obj.instrument.name))

    # Format background data responses for pandas dataframe and eventual printing
    try:
        background_data = BackgroundInfo.objects.values().filter(administration__in = administrations)

        BI_choices = {}

        fields = BackgroundInfo._meta.get_fields()
        for field in fields:
            if field.choices:
                field_choices = dict(field.choices)
                for k, v in field_choices.items():
                    if str(k) == str(v):
                        field_choices.pop(k, None)
                BI_choices[field.name] = {str(k):str(v) for k,v in field_choices.items()}

        new_background = pd.DataFrame.from_records(background_data).astype(str).replace(BI_choices)
        new_background['administration_id'] = new_background['administration_id'].astype('int64')

    except:
        new_background = pd.DataFrame(columns = ['administration_id'] + background_header)


    # Try to combine background data and CDI responses
    try:
        background_answers = pd.merge(new_background, melted_answers, how='outer', on = 'administration_id')
    except:
        background_answers = pd.DataFrame(columns = list(new_background) + list(melted_answers))

    # Try to format administration data for pandas dataframe
    try:
        admin_data = pd.DataFrame.from_records(administrations.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'})
    except:
        admin_data = pd.DataFrame(columns = admin_header)
    
    # Replace study ID# with actual study name
    admin_data['study_name'] = study_obj.name

    # Merge administration data into already combined background/CDI form dataframe
    combined_data = pd.merge(admin_data, background_answers, how='outer', on = 'administration_id')

    # Recreate link for administration
    test_url = ''.join(['http://', get_current_site(request).domain, reverse('administer_cdi_form', args=['a'*64])]).replace('a'*64+'/','')
    combined_data['link'] = test_url + combined_data['link']

    # If there are any missing columns (e.g., all test-takers for one study did not answer an item so it does not appear in database responses), add the empty columns in and don't break!
    missing_columns = list(set(model_header) - set(combined_data.columns))
    if missing_columns:
        combined_data = combined_data.reindex(columns = np.append( combined_data.columns.values, missing_columns))

    # Organize columns  
    combined_data = combined_data[admin_header + background_header + model_header ]

    # Turn pandas dataframe into a CSV
    combined_data.to_csv(response, encoding='utf-8', index=False)

    # Return CSV
    return response


@login_required
def download_dictionary(request, study_obj): # Download dictionary for instrument, lists relevant information for each item
    response = HttpResponse(content_type='text/csv') # Format the response as a CSV
    response['Content-Disposition'] = 'attachment; filename='+study_obj.instrument.name+'_dictionary.csv''' # Name CSV

    raw_item_data = model_map(study_obj.instrument.name).values('itemID','item_type','category','definition','gloss') # Grab the relevant variables within the appropriate instrument model
    item_data = pd.DataFrame.from_records(raw_item_data)
    item_data['definition'] = item_data['definition'].apply(lambda x: re.sub("__", "", x))
    item_data[['itemID','item_type','category','definition','gloss']].to_csv(response, encoding='utf-8', index=False) # Convert nested dictionary into a pandas dataframe and then into a CSV

    # Return CSV
    return response    

@login_required
def download_links(request, study_obj, administrations = None): # Download only the associated administration links instead of the whole data spreadsheet

    response = HttpResponse(content_type='text/csv') # Format response as a CSV
    response['Content-Disposition'] = 'attachment; filename='+study_obj.name+'_links.csv''' # Name CSV

    if administrations is None:
        administrations = administration.objects.filter(study = study_obj)

    admin_data = pd.DataFrame.from_records(administrations.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'}) # Grab variables from administration objects
    admin_data = admin_data[['study_name','subject_id', 'repeat_num', 'administration_id','link']] # Organize columns

    admin_data['study_name'] = study_obj.name # Replace study ID number with actual study name

    # Recreate administration links and add them to dataframe
    test_url = ''.join(['http://', get_current_site(request).domain, reverse('administer_cdi_form', args=['a'*64])]).replace('a'*64+'/','')
    admin_data['link'] = test_url + admin_data['link']
    admin_data.to_csv(response, encoding='utf-8', index=False) # Convert dataframe into a CSV

    # Return CSV
    return response

def write_to_zip(x, zf, vocab_start):
    curr_name = "{0}_S{1}_{2}".format(x['study_name'], x['subject_id'], x['repeat_num'])
    vocab_string = x[vocab_start:].to_string(header = False, index = False).replace('\n','').encode("utf-8")
    demo_string = ("{:<25}"*(vocab_start)).format(*x[0:vocab_start].replace(r'', np.nan, regex=True))
    string_to_write = demo_string + vocab_string
    zf.writestr("{}.txt".format(curr_name), string_to_write)

@login_required
def download_cdi_format(request, study_obj, administrations = None):
    outfile = StringIO.StringIO()
    
    if administrations is not None:
        completed_admins = administrations.filter(completed = True)
    else:
        completed_admins = administration.objects.filter(study = study_obj, completed = True)

    r = re.compile('item_[0-9]{1,3}')

    model_header = filter(r.match, get_model_header(study_obj.instrument.name))
    admin_header = ['study_name', 'subject_id','repeat_num', 'completed', 'last_modified']
    background_header = ['age','sex','zip_code','birth_order', 'birth_weight_lb', 'birth_weight_kg', 'multi_birth_boolean','multi_birth', 'born_on_due_date', 'early_or_late', 'due_date_diff', 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income', 'child_hispanic_latino', 'child_ethnicity', 'caregiver_info', 'other_languages_boolean', 'language_days_per_week', 'language_hours_per_day', 'ear_infections_boolean', 'hearing_loss_boolean', 'vision_problems_boolean', 'illnesses_boolean', 'services_boolean','worried_boolean','learning_disability_boolean']

    answers = administration_data.objects.values('administration_id', 'item_ID', 'value').filter(administration_id__in = completed_admins)
    melted_answers = pd.DataFrame.from_records(answers).pivot(index='administration_id', columns='item_ID', values='value')
    melted_answers.reset_index(level=0, inplace=True)

    missing_columns = [x for x in model_header if x not in melted_answers.columns]

    if missing_columns:
        melted_answers = melted_answers.reindex(columns = np.append(melted_answers.columns.values, missing_columns))

    new_answers = melted_answers

    new_answers.ix[:,1:] = new_answers.ix[:,1:].applymap(str)

    if study_obj.instrument.form == 'WG':
        for c in new_answers.columns[1:]:
            new_answers = new_answers.replace({c: {'nan': 0, 'none': 0, 'None': 0, 'understands': 1, 'produces': 2, 'simple': 1, 'complex': 2, 'no': 0, 'yes': 1, 'not yet': 0, 'sometimes': 1, 'often': 2, 'never': 0}})
    elif study_obj.instrument.form == 'WS':
        for c in new_answers.columns[1:]:
            new_answers = new_answers.replace({c: {'nan': 0, 'none': 0, 'None': 0, 'produces': 1, 'simple': 1, 'complex': 2, 'no': 0, 'yes': 1, 'not yet': 0, 'sometimes': 1, 'often': 2, 'never': 0}})

    background_data = BackgroundInfo.objects.values().filter(administration__in = completed_admins)
    new_background = pd.DataFrame.from_records(background_data)

    admin_data = pd.DataFrame.from_records(completed_admins.values()).rename(columns = {'id':'administration_id', 'study_id': 'study_name', 'url_hash': 'link'})
    admin_data['study_name'] = study_obj.name # Replace study ID number with actual study name

    background_answers = pd.merge(new_background, new_answers, how='outer', on = 'administration_id')
    combined_data = pd.merge(admin_data, background_answers, how='outer', on = 'administration_id')
    combined_data = combined_data[admin_header + background_header + model_header ]
    combined_data['last_modified'] = combined_data['last_modified'].dt.strftime('%Y-%m-%d %H:%M %Z')
    combined_data['annual_income'] = combined_data['annual_income'].apply(lambda x: 0 if x == 'Prefer not to disclose' else x)
    vocab_start = combined_data.columns.values.tolist().index('item_1')

    with zipfile.ZipFile(outfile, 'w') as zf:
        combined_data.apply(lambda x: write_to_zip(x, zf, vocab_start), axis = 1)
    zf.close()
    response = HttpResponse(outfile.getvalue(), content_type="application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % study_obj.name
    return response

@login_required
def console(request, study_name = None, num_per_page = 20): # Main giant function that manages the interface page
    refresh = False
    if request.method == 'POST' : # If submitting data, make sure that study is allowed to be edited by current user
        data = {}
        permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
        if permitted : # If user is permitted to update study
            study_obj = study.objects.get(researcher= request.user, name= study_name) # Grab study object
            ids = request.POST.getlist('select_col') # Get the list of administrations with a clicked checkbox
            if all([x.isdigit() for x in ids]): # Check that the administration numbers are all numeric
                if 'administer-selected' in request.POST: # If the 'Re-administer Participants' button was clicked
                    num_ids = map(int, ids) # Force numeric IDs into a list of integers
                    new_administrations = []
                    sids_created = set()

                    for nid in num_ids: # For each ID number
                        admin_instance = administration.objects.get(id = nid) # Grab the associated administration object
                        sid = admin_instance.subject_id # Pull subject ID from the administration object (unique to each study but not that whole database)
                        if sid in sids_created:
                            continue
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count() # Count the number of administrations previously given to this subject within this study
                        new_administrations.append(administration(study =study_obj, subject_id = sid, repeat_num = old_rep+1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=14))) # Create a new administration based off the # of previously completed participants
                        sids_created.add(sid) # Add new administration to the set of to-be-added administrations

                    administration.objects.bulk_create(new_administrations) # Add new administrations to administration model en masse
                    refresh = True # Refresh page to reflect table changes

                elif 'delete-selected' in request.POST: # If 'Delete Selected Data' was clicked
                    num_ids = list(set(map(int, ids))) # Force ID #s into a list of integers
                    administration.objects.filter(id__in = num_ids).delete() # Delete administrations with IDs found in the list of to-be-deleted IDs
                    refresh = True # Refresh page to reflect table changes

                elif 'download-links' in request.POST: # If 'Download Selected Data (Links)' was clicked
                    administrations = []
                    num_ids = list(set(map(int, ids))) # Force IDs into a list of integers
                    administrations = administration.objects.filter(id__in = ids) # Grab a queryset of administration objects with administration IDs found in list
                    return download_links(request, study_obj, administrations) # Send queryset to download_links function to return a CSV of subject data
                    refresh = True # Refresh page to reflect table changes


                elif 'download-selected' in request.POST: # If 'Download Selected Data' was clicked
                    num_ids = list(set(map(int, ids))) # Force IDs into a list of integers
                    administrations = administration.objects.filter(id__in = num_ids) # Grab a queryset of administration objects with administration IDs found in list
                    return download_data(request, study_obj, administrations) # Send queryset to download_data function to return a CSV of subject data
                    refresh = True # Refresh page to reflect table changes

                elif 'delete-study' in request.POST: # If 'Delete Study' button is clicked
                    study_obj.active = False # soft delete
                    study_obj.save()
                    study_name = None # Clear current study_name in interface
                    refresh = True # Refresh page

                elif 'download-study-csv' in request.POST: # If 'Download Data' button is clicked
                    administrations = administration.objects.filter(study = study_obj) # Grab a queryset of administration objects within study
                    return download_data(request, study_obj, administrations) # Send queryset to download_data and receive a CSV of responses
                
                elif 'download-study-scoring' in request.POST: # If 'Download Data' button is clicked
                    administrations = administration.objects.filter(study = study_obj) # Grab a queryset of administration objects within study
                    return download_cdi_format(request, study_obj, administrations)        

                elif 'download-study-scoring-selected' in request.POST: # If 'Download Data' button is clicked
                    num_ids = list(set(map(int, ids)))
                    administrations = administration.objects.filter(id__in = num_ids) # Grab a queryset of administration objects within study
                    return download_cdi_format(request, study_obj, administrations)                                     

                elif 'download-dictionary' in request.POST: # If 'Download Dictionary Data' button is clicked
                    return download_dictionary(request, study_obj) # Send study object to download_dictionary and receive a CSV of item data

                elif 'view_all' in request.POST: # If 'Show All' or 'Show 20' button is clicked
                    if request.POST['view_all'] == "Show All": # If description clicked was 'Show All'
                        num_per_page = administration.objects.filter(study = study_obj).count() # Update num_per_page to the number of administration objects within study
                    elif request.POST['view_all'] == "Show 20": # If description clicked was 'Show 20'
                        num_per_page = 20 # Set num_per_page to 20
                    refresh = True # Refresh page

    if request.method == 'GET' or refresh: # If fetching data for console rendering
        username = None # Set username to None at first
        if request.user.is_authenticated: # If logged in (should be)
            username = request.user.username # Set username to current user's username

        researcher_obj, created = researcher.objects.get_or_create(user = request.user)

        context = dict() # Create a dictionary of data related to template rendering such as username, studies associated with username, information on currently viewed study, and number of administrations to show.
        context['username'] =  username 
        context['studies'] = study.objects.filter(researcher = request.user, active = True).order_by('id')
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
            except:
                pass
        return render(request, 'researcher_UI/interface.html', context) # Render interface template

@login_required 
def rename_study(request, study_name): # Function for study settings modal
    data = {}
    form_package = {}
    #check if the researcher exists and has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)
    age_range = NumericRange(study_obj.min_age, study_obj.max_age)

    if request.method == 'POST' : # If submitting data
        form = RenameStudyForm(study_name, request.POST, instance = study_obj, age_range = age_range) # Grab submitted form

        # Mark these variables as None for later population
        raw_gift_codes = None
        all_new_codes = None
        old_codes = None
        amount_regex = None

        if form.is_valid(): # If form passed validation checks in forms.py

            # Grab submitted data along with username
            researcher = request.user
            new_study_name = form.cleaned_data.get('name')
            raw_gift_codes = form.cleaned_data.get('gift_codes')
            raw_gift_amount = form.cleaned_data.get('gift_amount')
            raw_test_period = form.cleaned_data.get('test_period')

            new_age_range = form.cleaned_data.get('age_range')
            study_obj.min_age = new_age_range.lower
            study_obj.max_age = new_age_range.upper

            study_obj = form.save(commit=False) # Save object but do not commit to database just yet
            study_obj.test_period = raw_test_period if (raw_test_period >= 1 and raw_test_period <= 14) else 14 # Check that entered test period is within the 1-14 range. If not, set to default (14)

            if new_study_name != study_name: # If the study name has changed
                if study.objects.filter(researcher = researcher, name = new_study_name).exists() or '/' in new_study_name: # Check whether the new name has already been taken by this researcher
                    study_obj.name = study_name # If not, update study name

            study_obj.save() # Commit study object to database

            new_study_name = study_obj.name

            if raw_gift_codes: # If gift card codes were entered
                # Parse text into a list of valid gift codes 
                new_payment_codes = []
                used_codes = []
                gift_codes = re.split('[,;\s\t\n]+', raw_gift_codes)
                gift_regex = re.compile(r'^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{4}$')
                gift_type = "Amazon"
                gift_codes = filter(gift_regex.search, gift_codes)                

                try:
                    amount_regex = Decimal(re.search('([0-9]{1,3})?.[0-9]{2}', raw_gift_amount).group(0)) # Try to parse entered monetary amount into proper currency format
                except:
                    pass

                if amount_regex: # If monetary amount was properly registered

                    for gift_code in gift_codes: # For each code
                        if not payment_code.objects.filter(payment_type = gift_type, gift_code = gift_code).exists(): # Check that the code is unique within the database
                            new_payment_codes.append(payment_code(study =study_obj, payment_type = gift_type, gift_code = gift_code, gift_amount = amount_regex)) # Add code to the list of to-be-added codes
                        else:
                            used_codes.append(gift_code) # If code was already in database, place into the list of non-unique codes
                if not used_codes: # If all the entered codes were unique, pass the unique codes check
                    all_new_codes = True

            # Error reporting. Can be confusing because of the different error combinations!
            if raw_gift_codes: # If gift codes were entered
                if not all_new_codes or not amount_regex: # And there were non-unique codes or the monetary value was not properly entered
                    data['stat'] = "error"; # Flag as error
                    err_msg = []
                    if not all_new_codes:
                        err_msg = err_msg + ['The following codes are already in the database:'] + used_codes; # Print error for non-unique codes and display all flagged entries
                    if not amount_regex:
                        err_msg = err_msg + [ "Please enter in a valid amount for \"Amount per Card\""]; # Print error and ask for re-entry of monetary value

                    data['error_message'] = "<br>".join(err_msg); # Join error messages together
                    return HttpResponse(json.dumps(data), content_type="application/json") # Display error message
                else:
                    if all_new_codes: # If there were no errors with gift card code entry
                        payment_code.objects.bulk_create(new_payment_codes) # Add gift card codes to database
                        data['stat'] = "ok"; # Mark as entry 'ok'
                        data['redirect_url'] = "/interface/study/"+new_study_name+"/"; # Set to redirect back to interface
                        return HttpResponse(json.dumps(data), content_type="application/json") 
            else:
                data['stat'] = "ok"; # Mark as entry 'ok'
                data['redirect_url'] = "/interface/study/"+new_study_name+"/"; # Set to redirect back to interface
                return HttpResponse(json.dumps(data), content_type="application/json")            

        else:
            data['stat'] = "re-render"; # Mark as entry needing re-rendering
            form_package['form'] = form
            form_package['form_name'] = 'Update Study'
            form_package['allow_payment'] = study_obj.allow_payment
            return render(request, 'researcher_UI/add_study_modal.html', form_package) # Reload 'Update Study' modal
    else:

        form = RenameStudyForm(instance = study_obj, old_study_name = study_obj.name, age_range = age_range)
        form_package['form'] = form
        form_package['form_name'] = 'Update Study'
        form_package['allow_payment'] = study_obj.allow_payment
        form_package['min_age'] = age_range.lower
        form_package['max_age'] = age_range.upper
        return render(request, 'researcher_UI/add_study_modal.html', form_package) # Reload 'Update Study' modal
        
@login_required 
def add_study(request): # Function for adding studies modal
    data = {}
    researcher = request.user # Get username for logged-in user

    if request.method == 'POST' : # If submitting data
        form = AddStudyForm(request.POST, researcher = researcher) # Grab submitted form

        if form.is_valid(): # If form passed validation checks in forms.py
            print "Valid form"
            study_instance = form.save(commit=False) # Save study object but do not commit to database just yet
            study_name = form.cleaned_data.get('name')
            age_range = form.cleaned_data.get('age_range')
            
            study_instance.active = True

            try:
                study_instance.min_age = age_range.lower
                study_instance.max_age = age_range.upper
            except:
                study_instance.min_age = study_instance.instrument.min_age
                study_instance.max_age = study_instance.instrument.max_age

            slash_in_name = True if '/' in study_name else None
            not_unique_name = True if study.objects.filter(researcher = researcher, name = study_name).exists() else None

            study_instance.researcher = researcher

            if not form.cleaned_data.get('test_period'):
                study_instance.test_period = 14

            if not slash_in_name and not not_unique_name: # If the researcher does not already have a study with the given name

                study_instance.save() # Save study to database
                data['stat'] = "ok"; # Mark entry as 'ok'
                data['redirect_url'] = "/interface/study/"+study_name+"/";
                return HttpResponse(json.dumps(data), content_type="application/json") # Redirect back to interface
            elif not_unique_name: # If study with same name already exists
                data['stat'] = "error"; # Mark entry as 'error'
                data['error_message'] = "Study already exists; Use a unique name";
                return HttpResponse(json.dumps(data), content_type="application/json") # Display error message about non-unique study back to user
            elif slash_in_name:
                data['stat'] = "error"; # Mark entry as 'error'
                data['error_message'] = "Study name has a forward slash ('/') inside. Please remove or replace this character.";
                return HttpResponse(json.dumps(data), content_type="application/json") # Display error message about non-unique study back to user                
        else: # If form failed validation checks
            print "Invalid form"
            data['stat'] = "re-render"; # Re-render form
            return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})
    else: # If fetching modal
        form = AddStudyForm(researcher=researcher) # Pull up blank form and render
        return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})


@login_required 
def add_paired_study(request): # Function for pairing studies modal
    data = {}
    researcher = request.user # Get username for logged-in user

    if request.method == 'POST' : # If submitting data
        form = AddPairedStudyForm(request.POST) # Grab submitted form
        if form.is_valid(): # If form passed validation checks in forms.py
            # Grab submitted fields
            study_group = form.cleaned_data.get('study_group')
            paired_studies = form.cleaned_data.get('paired_studies')
            permissions = []
            for one_study in paired_studies: # For each study selected for grouping
                permitted = study.objects.filter(researcher = researcher,  name = one_study).exists() # Make sure that user is allowed to edit this study (they created it themselves)
                permissions.append(permitted)
                if permitted: # If user is permitted to edit
                    study_obj = study.objects.get(researcher = researcher,  name = one_study) # Get the study object                   
                    study_obj.study_group = study_group # Update study group
                    study_obj.save() # Save updated object to database

            if all(True for permission in permissions): # If user was allowed to edit all the studies they selected
                data['stat'] = "ok"; # Mark entry as 'ok'
                data['redirect_url'] = "/interface/"; # Redirect back to interface
                return HttpResponse(json.dumps(data), content_type="application/json")

            else: # If one or more studies were not open for editing
                data['stat'] = "error"; # Mark entry as 'error'
                data['error_message'] = "Study group already exists; Use a unique name"; # Print error message
                return HttpResponse(json.dumps(data), content_type="application/json")
        else: # If form did not pass validation checks in forms.py
            data['stat'] = "re-render"; # Re-render form
            return render(request, 'researcher_UI/add_paired_study_modal.html', {'form': form})
    else: # If fetching form
        form = AddPairedStudyForm(researcher = researcher) # Pull up a blank copy of form and render
        return render(request, 'researcher_UI/add_paired_study_modal.html', {'form': form})

def random_url_generator(size=64, chars='0123456789abcdef'): # Function for generating a string of random characters from a set. Meant for generating unique URLs for each administration.
    return ''.join(random.choice(chars) for _ in range(size))


@login_required 
def administer_new(request, study_name): # For creating new administrations
    data = {}
    context = dict()
    # Check if the researcher has permissions over the study
    permitted = study.objects.filter(researcher = request.user,  name = study_name).exists()
    study_obj = study.objects.get(researcher= request.user, name= study_name)

    if request.method == 'POST' : # If submitting data
        if permitted : # Check if user is allowed to update study
            params = dict(request.POST) # Take submitted data and format into a dictionary
            validity = True
            data['error_message'] = ''
            raw_ids_csv = request.FILES['subject-ids-csv'] if 'subject-ids-csv' in request.FILES else None # If a CSV of subject IDs was uploaded, hold onto it

            if params['new-subject-ids'][0] == '' and params['autogenerate-count'][0] == '' and raw_ids_csv is None: # Make sure that one of the entry fields has a response in it before attempting to create administrations
                validity = False
                data['error_message'] += "Form is empty\n" # Display error message if all fields are empty

            if raw_ids_csv: # If a CSV of subject IDs was uploaded
                if 'csv-header' in request.POST: # If CSV was marked as having a header row
                    ids_df = pd.read_csv(raw_ids_csv) # Convert CSV into a pandas dataframe
                    if request.POST['subject-ids-column']: # If the column name was specified in form
                        subj_column = request.POST['subject-ids-column']
                        if subj_column in ids_df.columns: # If the specifiied column name exists within that CSV
                            ids_to_add = ids_df[subj_column] # Load the data from that column
                            ids_type =  ids_to_add.dtype # Check the column data type
                        else: # If that column does not exist in the CSV
                            ids_type = 'missing' # Flag as missing

                    else: # If no column name was specified
                        ids_to_add = ids_df[ids_df.columns[0]] # Load the first column in the CSV
                        ids_type =  ids_to_add.dtype # Check column data type

                else: # If CSV was not marked as having a header row
                    ids_df = pd.read_csv(raw_ids_csv, header = None) # Convert CSV into a pandas dataframe
                    ids_to_add = ids_df[ids_df.columns[0]] # Load the first column in CSV
                    ids_type =  ids_to_add.dtype # Check column data type

                if ids_type != 'int64': # If the loaded column data is not integer-only
                    validity = False # Mark as invalid
                    if 'csv-header' not in request.POST: # If the CSV was specified as NOT having a header
                        data['error_message'] += "Non integer subject ids. Make sure first row is numeric\n" # Save this error message
                    else: # If the CSV was specified as having a header
                        if ids_type == 'missing': # If the column was marked as missing
                            data['error_message'] += "Unable to find specified column. Check for any typos." # Save this error message
                        else: # If the column is present in the CSV
                            data['error_message'] += "Non integer subject ids\n" # Save this error message


            if params['new-subject-ids'][0] != '': # If there was text entered in the textbox field
                subject_ids = re.split('[,;\s\t\n]+', str(params['new-subject-ids'][0])) # Parse string into a list of string IDs by commas, semicolons, spaces, tabs, and new lines
                subject_ids = filter(None, subject_ids)
                subject_ids_numbers = all([x.isdigit() for x in subject_ids]) # Check that all string IDs are only digits
                if not subject_ids_numbers: # If not all the string IDs are digits
                    validity = False # Mark as invalid
                    data['error_message'] += "Non integer subject ids\n" # Save this error message

            if params['autogenerate-count'][0] != '': # If there was text entered into the autogenerate field
                autogenerate_count = params['autogenerate-count'][0] # Grab entry
                autogenerate_count_isdigit = autogenerate_count.isdigit() # Check that the text is only digits
                if not autogenerate_count_isdigit: # If the text is not digit-only
                    validity = False # Mark as invalid
                    data['error_message'] += "Non integer number of IDs to autogenerate\n" # Save this error message

            if validity: # If the entries were valid
                new_administrations = [] # Create a list for adding new administration objects
                test_period = int(study_obj.test_period) # Note test period for study
                if raw_ids_csv: # If a CSV was uploaded

                    subject_ids = list(np.unique(ids_to_add.tolist())) # Convert pandas dataframe column into a python list

                    for sid in subject_ids: # For each ID within the list
                        new_hash = random_url_generator() # Generate a unique hash ID
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count() # Count the number of administrations previously given to this subject ID
                        if not administration.objects.filter(study = study_obj, subject_id = sid, repeat_num = old_rep + 1).exists():
                            administration.objects.create(study = study_obj, subject_id = sid, repeat_num = old_rep + 1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now() + datetime.timedelta(days=test_period))

                if params['new-subject-ids'][0] != '': # If there was text in the new_subject_ids field
                    subject_ids = re.split('[,;\s\t\n]+', str(params['new-subject-ids'][0])) # Parse by numerous text delimiters
                    subject_ids = filter(None, subject_ids)
                    subject_ids = list(np.unique(map(int, subject_ids))) # Convert into a list of integers
                    for sid in subject_ids: # For each subject ID
                        new_hash = random_url_generator() # Generate a unique hash ID
                        old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count() # Count the number of administrations previously given to this subject ID
                        if not administration.objects.filter(study = study_obj, subject_id = sid, repeat_num = old_rep + 1).exists():
                            administration.objects.create(study = study_obj, subject_id = sid, repeat_num = old_rep + 1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now() + datetime.timedelta(days = test_period))


                if params['autogenerate-count'][0]!='': # If there was text in the autogenerate field
                    autogenerate_count = int(params['autogenerate-count'][0]) # Convert the text entry into an integer
                    if study_obj.study_group:
                        related_studies = study.objects.filter(researcher = study_obj.researcher, study_group = study_obj.study_group)
                    else:
                        related_studies = study.objects.filter(id=study_obj.id)
                    max_subject_id = administration.objects.filter(study__in=related_studies).aggregate(Max('subject_id'))['subject_id__max'] # Find the subject ID with the largest number within this study. For example, a study with subject IDs like '3','5',and '25' would get a '25' in this field.
                    if max_subject_id is None: # If there is no max subject ID number (study has 0 participants)
                        max_subject_id = 0 # Mark the max as 0
                    for sid in range(max_subject_id+1, max_subject_id+autogenerate_count+1): # For each to-be-created subject ID
                        new_hash = random_url_generator() # Generate a unique hash ID
                        administration.objects.create(study =study_obj, subject_id = sid, repeat_num = 1, url_hash = new_hash, completed = False, due_date = datetime.datetime.now() + datetime.timedelta(days = test_period))

                # administration.objects.bulk_create(new_administrations) # Add the list of new administration objects to the database
                data['stat'] = "ok"; # Mark entry as 'ok'
                data['redirect_url'] = "/interface/study/"+study_name+"/?sort=-created_date"; # Redirect to researcher interface with newest administrations at top of table
                data['study_name'] = study_name
                return HttpResponse(json.dumps(data), content_type="application/json")
            else: # If entries were invalid
                data['stat'] = "error"; # Mark as error
                return HttpResponse(json.dumps(data), content_type="application/json")
        else: # If user is not allowed to edit study
            data['stat'] = "error"; # Mark entry as error
            data['error_message'] = "permission denied"; # Print this error message
            data['redirect_url'] = "interface/"; # Redirect to interface
            return HttpResponse(json.dumps(data), content_type="application/json")
    else: # If fetching blank form
        context['username'] = request.user.username 
        context['study_name'] = study_name
        context['study_group'] = study_obj.study_group
        return render(request, 'researcher_UI/administer_new_modal.html', context) # Render blank form with added context of username, current study name, and study group.

def administer_new_parent(request, username, study_name): # For creating single administrations. Does not require a log-in. Participants can generate their own single-use administration if given the proper link,
    data={}
    researcher = User.objects.get(username = username) # Get researcher's username. Different method because current user may not be the researcher and may not be logged in
    study_obj = study.objects.get(name= study_name, researcher = researcher) # Find the study object associated with the researcher and study name
    subject_cap = study_obj.subject_cap # Get the subject cap for this study
    test_period = int(study_obj.test_period) # Get the testing period for this study
    completed_admins = administration.objects.filter(study = study_obj, completed = True).count() # Count the number of completed administrations within this study
    bypass = request.GET.get('bypass', None) # Check if user clicked the link to bypass study cap (studies that allow for payment will not pay participants in this case)
    let_through = None # By default, users are not given access to administration and must be approved
    prev_visitor = 0 
    visitor_ip = str(get_ip(request)) # Get IP address for current visitor
    completed = int(request.get_signed_cookie('completed_num', '0')) # Check if there is a cookie stored on device for a previously completed administration
    if visitor_ip: # If the visitor IP was successfully pulled
        prev_visitor = ip_address.objects.filter(ip_address = visitor_ip).count() # Check if IP address was logged previously in the database (only logged for specific studies under the langcoglab account. This is under Stanford's IRB approval)

    if (prev_visitor < 1 and completed < 2) or request.user.is_authenticated: # If the user if the user has not visited an excessive number of times based on IP logs and cookies or if they are logged-in (therefore a vetted researcher) 
        if completed_admins < subject_cap: # If the number of completed tests has not reached the subject cap
            let_through = True # Mark as allowed
        elif subject_cap is None: # If there was no subject cap sent up
            let_through = True # Mark as allowed
        elif bypass: # If the user explicitly wanted to continue with the test despite being told they would not be compensated
            let_through = True # Mark as allowed

    if let_through: # If marked as allowed
        subject_id = request.GET.get("subject_id") # used for wordful RedCap study
        if subject_id:
            num_admins = administration.objects.filter(study=study_obj, subject_id=subject_id).count()
            if num_admins == 0: # create first administration
                requests.get("http://wordful-flask.herokuapp.com/addEmailAddressToStudy", params={
                    "email":request.GET.get("email"),
                    "studyId":"ContinuousCDI" # hardcode study id for wordful
                    })
                admin = administration(study=study_obj, subject_id=subject_id, repeat_num=1)
                admin.url_hash = random_url_generator()
                admin.completed = False
                admin.due_date = timezone.now()+datetime.timedelta(days=test_period)
                admin.bypass = True
                admin.save()
            elif num_admins == 1: # check if this is final cdi or if user is continuing first CDI
                if request.GET.get("final_cdi"):
                    admin = administration.objects.create(
                        study=study_obj,
                        subject_id=subject_id,
                        repeat_num=2,
                        url_hash=random_url_generator(),
                        completed=False,
                        due_date=datetime.datetime.now() + datetime.timedelta(days=14)
                    )  # Create a new administration based off the # of previously completed participants
                else:
                    admin = administration.objects.get(study=study_obj, subject_id=subject_id, repeat_num = 1)
            else: # return final CDI. can only have 2 in this study
                admin = administration.objects.get(study=study_obj, subject_id=subject_id, repeat_num=2)
            return redirect(reverse('administer_cdi_form', args=[admin.url_hash]))


        if study_obj.study_group:
            related_studies = study.objects.filter(researcher=researcher, study_group=study_obj.study_group)
            max_subject_id = administration.objects.filter(study__in=related_studies).aggregate(Max('subject_id'))['subject_id__max']
        else:
            max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max'] # Find the subject ID in this study with the highest number

        if max_subject_id is None: # If the max subject ID could not be found (e.g., study has 0 participants)
            max_subject_id = 0 # Mark as zero
        new_admin = administration.objects.create(study =study_obj, subject_id = max_subject_id+1, repeat_num = 1, url_hash = random_url_generator(), completed = False, due_date = datetime.datetime.now()+datetime.timedelta(days=test_period)) # Create an administration object for participant within database
        new_hash_id = new_admin.url_hash # Note the generated hash ID
        if bypass: # If the user explicitly wanted to continue with the test despite being told they would not be compensated
            new_admin.bypass = True # Mark administation object with 'bypass'
            new_admin.save() # Update object in database
        redirect_url = reverse('administer_cdi_form', args=[new_hash_id]) # Generate the administration URL given the object's hash ID
    else: # If not marked as allowed
        redirect_url = reverse('overflow', args=[username, study_name]) # Generate URL for overflowed participants. May or may not have option for bypass depending on context (IP address and cookies)
    return redirect(redirect_url) # Redirect to generated URL

def overflow(request, username, study_name): # Page for overflowed studies. For studies where subject cap has been reached or participant is noted as having excessive visits 
    data = {}
    data['username'] = username # Get researcher user name
    data['study_name'] = study_name # Get study's name
    researcher = User.objects.get(username = username) # Get researcher's username. Different method because current user may not be the researcher and may not be logged in
    study_obj = study.objects.get(name= study_name, researcher = researcher) 
    data['title'] = study_obj.instrument.verbose_name
    visitor_ip = str(get_ip(request)) # Get visitor's IP address
    prev_visitor = 0
    if (visitor_ip and visitor_ip != 'None'): # If visitor IP address was properly caught
        prev_visitor = ip_address.objects.filter(ip_address = visitor_ip).count() # Check if IP address was logged previously in the database (only logged for specific studies under the langcoglab account. This is under Stanford's IRB approval)
    if prev_visitor > 0 and not request.user.is_authenticated: # If IP address appears in logs and the user is not logged-in (cannot tell if a vetted reseacher)
        data['repeat'] = True # Mark as a repeat visitor. Will not be given the option to bypass in template
    data['bypass_url'] = reverse('administer_new_parent', args=[username, study_name]) + '?bypass=true'


    return render(request, 'cdi_forms/overflow.html', data) # Render overflow page

def try_parsing_date(text):
    date_formats = ('%Y.%m.%d', '%Y-%m-%d', '%Y/%m/%d','%m.%d.%Y', '%m-%d-%Y', '%m/%d/%Y',)
    for fmt in date_formats:
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def make_unicode(s):
    if type(s) != unicode:
        s =  s.decode('utf-8')
        return s
    else:
        return s

def processDemos(csv_file, demo_list = None):
    recoded_df = csv_file.where((pd.notnull(csv_file)), None)
    PROJECT_ROOT = settings.BASE_DIR

    if demo_list:
        for col in demo_list:
            if 'boolean' in col or col == 'born_on_due_date':
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in [0,1] else 2)
            elif col == 'child_hispanic_latino':
                recoded_df[col] = recoded_df[col].apply(lambda x: bool(x) if x in [0,1] else None)
            elif col == 'birth_order':
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in range(1,10) else 0).astype('int')
            elif col in ['ear_infections', 'hearing_loss', 'illnesses', 'learning_disability', 'multi_birth', 'services', 'vision_problems', 'worried']:
                recoded_df[col] = recoded_df[col].apply(lambda x: make_unicode(x) if x and len(x) <= 1000 else None)
            elif col == 'language_from':
                recoded_df[col] = recoded_df[col].apply(lambda x: make_unicode(x) if x and len(x) <= 50 else None)
            elif 'yob' in col:
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in range(1950, datetime.datetime.today().year + 1) else 0).astype('int')
            elif 'education' in col:
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in range(1,24) else 0).astype('int')
            elif col == 'early_or_late':
                recoded_df[col] = recoded_df[col].apply(lambda x: make_unicode(x.lower()) if x and x.lower() in ['early', 'late'] else None)
            elif col == 'zip_code':
                def parse_zipcode(c):
                    if c and re.match("(\d{3}([*]{2})?)", c):
                        if Zipcode.objects.filter(zip_prefix = c).exists():
                            return Zipcode.objects.filter(zip_prefix = c).first().state
                        else:
                            return c + '**'
                    elif c and re.match("([A-Z]{2})", c):
                        return make_unicode(c)
                    else:
                        return u''
                recoded_df[col] = recoded_df[col].str[:3].apply(parse_zipcode)
            elif col == 'language_days_per_week':
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in range(1,8) else None)
            elif col == 'language_hours_per_day':
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in range(1,25) else None)
            elif col == 'due_date_diff':
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x >= 1 else None)
            elif col == 'caregiver_info':
                recoded_df[col] = recoded_df[col].apply(lambda x: int(x) if x in range(0,5) else 0)
            elif col == 'birth_weight_lb':
                def round_lb(c):
                    c = int(c * 2) / 2.0
                    c = 1.0 if c < 3.0 else c
                    c = 10.0 if c > 10.0 else c
                    return c 
                recoded_df[col] = recoded_df[col].apply(round_lb)
            elif col == 'birth_weight_kg':
                def round_kg(c):
                    c = int(c * 4) / 4.0
                    c = 1.0 if c < 1.5 else c
                    c = 5.0 if c > 5.0 else c
                    return c 
                recoded_df[col] = recoded_df[col].apply(round_kg)
            elif col == 'annual_income':
                recoded_df[col] = recoded_df[col].apply(lambda x: make_unicode(x) if x and x in dict(BackgroundInfo._meta.get_field(col).choices).keys() else u'Prefer not to disclose')                 
            elif col == 'child_ethnicity':
                recoded_df[col] = recoded_df[col].apply(lambda x: list(set(make_unicode(x).upper().split('/')) & set([u'N', u'H', u'W', u'B', u'A', u'O'])) if x else [])
            elif col == 'other_languages':
                lang_choices = [make_unicode(v['name']) for k,v in json.load(codecs.open(PROJECT_ROOT + '/languages.json', 'r', 'utf-8')).iteritems()]
                recoded_df[col] = recoded_df[col].apply(lambda x: list(set([y.strip() for y in make_unicode(x).split('/')]) & set(lang_choices)) if x else [])

    recoded_df = recoded_df.where((pd.notnull(recoded_df)), None)
    return recoded_df

def import_data(request, study_name):

    data = {}
    study_obj = study.objects.get(researcher= request.user, name= study_name)

    if request.method == 'POST' : # If submitting data
        form = ImportDataForm(request.POST, request.FILES, researcher = request.user, study = study_obj)

        if form.is_valid():
            PROJECT_ROOT = settings.BASE_DIR
            instruments_json = json.load(open(os.path.realpath(PROJECT_ROOT + '/static/json/instruments.json')))
            header_file_path = filter(lambda x: x['language'] == study_obj.instrument.language and x['form'] == study_obj.instrument.form, instruments_json)[0]['fillable_headers']
            pdf_header_df = pd.read_csv(open(os.path.realpath(PROJECT_ROOT + '/' +header_file_path)))

            default_dict = {
            'annual_income': u'Prefer not to disclose', 'birth_order': 0, 'birth_weight_kg': None,
            'birth_weight_lb': 0.0, 'born_on_due_date': 2, 'caregiver_info': 0,
            'child_ethnicity': [], 'child_hispanic_latino': None, 'due_date_diff': None,
            'ear_infections': None, 'ear_infections_boolean': 2, 'early_or_late': u'',
            'father_education': 0, 'father_yob': 0, 'hearing_loss': None,
            'hearing_loss_boolean': 2, 'illnesses': None, 'illnesses_boolean': 2,
            'language_days_per_week': None, 'language_from': None, 'language_hours_per_day': None,
            'learning_disability': None, 'learning_disability_boolean': 2, 'mother_education': 0,
            'mother_yob': 0, 'multi_birth': None, 'multi_birth_boolean': 2,
            'other_languages': [], 'other_languages_boolean': 2, 'services': None,
            'services_boolean': 2, 'vision_problems': None, 'vision_problems_boolean': 2,
            'worried': None, 'worried_boolean': 2, 'zip_code': u''
            }

            csv_file = pd.read_csv(request.FILES['imported_file'])
            demo_list = list(set(default_dict.keys()) & set(csv_file))

            csv_file = processDemos(csv_file, demo_list)
            admin_row = next(csv_file.iterrows())[1]
            error_msg = None
            new_admin_pks = []

            for index, admin_row in csv_file.iterrows():

                raw_sid = str(admin_row['name_of_child'])
                if raw_sid.isdigit():
                    sid = int(raw_sid)
                else:
                    error_msg = "Subject IDs must be numeric only."
                    break

                old_rep = administration.objects.filter(study = study_obj, subject_id = sid).count()

                try:
                    due_date = try_parsing_date(admin_row['date_today'])
                except ValueError:
                    error_msg = "Invalid date format. Please submit dates as MM-DD-YYYY or YYYY-MM-DD. '/' and '.' delimiters are alsoacceptable."
                    break

                new_admin = administration.objects.create(study = study_obj, subject_id = sid, repeat_num = old_rep + 1, url_hash = random_url_generator(), completed = True, completedBackgroundInfo = True, due_date = due_date, last_modified = due_date)
                new_admin_pks.append(new_admin.pk)

                if admin_row['gender'] == "m":
                    sex = u'M'
                elif admin_row['gender'] == "f":
                    sex = u'F'
                else:
                    sex = u'O'

                dot = due_date

                try:
                    dob = try_parsing_date(admin_row['birthdate'])
                except ValueError:
                    error_msg = "Invalid date format. Please submit dates as MM-DD-YYYY or YYYY-MM-DD. '/' and '.' delimiters are alsoacceptable."
                    break

                raw_age = dot - dob
                age = int(float(raw_age.days)/(365.2425/12.0))

                csv_dict = {
                'sex': sex,
                'age': age
                }

                background_dict = default_dict.copy()
                background_dict.update(csv_dict)

                if demo_list:
                    background_dict.update(dict(admin_row[demo_list]))

                try:
                    new_background, created = BackgroundInfo.objects.get_or_create(administration = new_admin, defaults = background_dict)
                except:
                    error_msg = "Error adding background information."
                    break

                fillable_items = pd.DataFrame({'pdf_header':admin_row.index, 'value':admin_row.values})
                cdi_responses = []
                cdi_responses_df = pd.merge(pdf_header_df, fillable_items, how='left', on='pdf_header')

                yes_list = ['yes', '1']
                no_list = ['no', '0']
                graded_list = ['not yet', 'sometimes', 'often']

                try:
                    for index, response_row in cdi_responses_df.iterrows():
                        item_value = None
                        raw_value = str(response_row['value']).lower()
                        if study_obj.instrument.form == 'WS':
                            if response_row['item_type'] in ['word', 'word_form', 'word_ending'] and raw_value in yes_list:
                                item_value = 'produces'
                            elif response_row['item_type'] in ['usage', 'ending', 'combine']:
                                item_value = raw_value
                            elif response_row['item_type'] == 'combination_examples':
                                item_value = str(response_row['value'])
                            elif response_row['item_type'] == 'complexity':
                                if raw_value in no_list + ['simple']:
                                    item_value = 'simple'
                                elif raw_value in yes_list + ['complex']:
                                    item_value = 'complex'
                        elif study_obj.instrument.form == 'WG':
                            if response_row['item_type'] == 'first_signs':
                                if raw_value in yes_list + no_list:
                                    item_value = 'yes' if raw_value in yes_list else 'no'
                            elif response_row['item_type'] == 'phrases' and raw_value in yes_list:
                                item_value = "understands"
                            elif response_row['item_type'] in ['starting_to_talk', 'gestures']:
                                if raw_value in graded_list:
                                    item_value = raw_value
                                elif raw_value in yes_list:
                                    item_value = 'yes'
                                elif raw_value in no_list:
                                    item_value = 'no'
                            elif response_row['item_type'] == 'word':
                                if raw_value in ['understands', '1']:
                                    item_value = 'understands'
                                elif raw_value in ['understands and says', 'produces', '2']:
                                    item_value = 'produces'
                        if item_value:
                            try:
                                cdi_responses.append(administration_data(
                                    administration = new_admin,
                                    item_ID = response_row['itemID'],
                                    value = item_value
                                ))
                            except:
                                error_msg = "Error importing item '%s' for subject_id '%s'" % (sid, response_row['itemID'])
                                # break
                    administration_data.objects.bulk_create(cdi_responses)
                except:
                    error_msg = "Error importing administration data. Check that only valid values are in item columns."
                    break

            if error_msg is None:
                data['stat'] = "ok"; # Mark entry as 'ok'
                data['redirect_url'] = reverse('console', args = [study_obj.name]); # Redirect back to interface
                return HttpResponse(json.dumps(data), content_type="application/json")
            else:
                administration.objects.filter(pk__in = new_admin_pks).delete()
                data['stat'] = "error"; # Mark entry as 'error'
                data['error_message'] = error_msg; # Print error message
                return HttpResponse(json.dumps(data), content_type="application/json")

        else: # If form did not pass validation checks in forms.py
            data['stat'] = "re-render"; # Re-render form
            return render(request, 'researcher_UI/import_data.html', {'form': form}) 

    else: # If fetching form
        form = ImportDataForm(researcher = request.user, study = study_obj) # Pull up a blank copy of form and render
        return render(request, 'researcher_UI/import_data.html', {'form': form})
