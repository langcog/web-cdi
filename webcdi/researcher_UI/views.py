# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import AddStudyForm, RenameStudyForm, AddPairedStudyForm
from .models import study, administration, administration_data, get_meta_header, get_background_header, payment_code, ip_address
import codecs, json, os, re, random, csv, datetime, cStringIO, math, StringIO, zipfile
from .tables  import StudyAdministrationTable
from django_tables2   import RequestConfig
from django.db.models import Max
from cdi_forms.views import model_map, get_model_header, background_info_form, prefilled_background_form
from cdi_forms.models import BackgroundInfo
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
import pandas as pd
import numpy as np
from django.urls import reverse
from decimal import Decimal
from django.contrib.sites.shortcuts import get_current_site
from ipware.ip import get_ip
from psycopg2.extras import NumericRange




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
    background_header = ['age','sex','zip_code','birth_order','multi_birth_boolean','multi_birth', 'birth_weight', 'born_on_due_date', 'early_or_late', 'due_date_diff', 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income', 'child_hispanic_latino', 'child_ethnicity', 'caregiver_info', 'other_languages_boolean','other_languages','language_from', 'language_days_per_week', 'language_hours_per_day', 'ear_infections_boolean','ear_infections', 'hearing_loss_boolean','hearing_loss', 'vision_problems_boolean','vision_problems', 'illnesses_boolean','illnesses', 'services_boolean','services','worried_boolean','worried','learning_disability_boolean','learning_disability']

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
        new_background = pd.DataFrame.from_records(background_data)

        if len(list(new_background)) > 0:
            for c in new_background.columns:
                try:
                    new_background = new_background.replace({c: dict(BackgroundInfo._meta.get_field(c).choices)}) # Replaces integer and single letter responses in dataframe with more easily interpreted choices that were originally given to test-takers. For instance, gender in database is stored as 'M' but is presented to test-takers and researchers as 'Male' for a lesser chance of misinterpretation
                except:
                    if 'boolean' in c or c == 'born_on_due_date': # Replace integer boolean responses with text responses (catches any columns missed by previous pass)
                        new_background = new_background.replace({c: {0: 'No', 1: 'Yes', 2: 'Prefer not to disclose'}})
                    elif c == 'child_hispanic_latino':
                        new_background = new_background.replace({c: {False: 'No', True: 'Yes'}})
        else:
            new_background = pd.DataFrame(columns = ['administration_id'] + background_header)

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

    raw_item_data = model_map(study_obj.instrument.name).objects.values('itemID','item_type','category','definition','gloss') # Grab the relevant variables within the appropriate instrument model
    item_data = pd.DataFrame.from_records(raw_item_data)
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
    background_header = ['age','sex','zip_code','birth_order','multi_birth_boolean','multi_birth', 'birth_weight', 'born_on_due_date', 'early_or_late', 'due_date_diff', 'mother_yob', 'mother_education','father_yob', 'father_education', 'annual_income', 'child_hispanic_latino', 'child_ethnicity', 'caregiver_info', 'other_languages_boolean', 'language_days_per_week', 'language_hours_per_day', 'ear_infections_boolean', 'hearing_loss_boolean', 'vision_problems_boolean', 'illnesses_boolean', 'services_boolean','worried_boolean','learning_disability_boolean']

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
                    study_obj.delete() # Delete study object
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
        context = dict() # Create a dictionary of data related to template rendering such as username, studies associated with username, information on currently viewed study, and number of administrations to show.
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
    if request.method == 'POST' : # If submitting data
        form = AddStudyForm(request.POST) # Grab submitted form

        if form.is_valid(): # If form passed validation checks in forms.py

            study_instance = form.save(commit=False) # Save study object but do not commit to database just yet
            researcher = request.user
            study_name = form.cleaned_data.get('name')

            age_range = form.cleaned_data.get('age_range')

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
            data['stat'] = "re-render"; # Re-render form
            return render(request, 'researcher_UI/add_study_modal.html', {'form': form, 'form_name': 'Add New Study'})
    else: # If fetching modal
        form = AddStudyForm() # Pull up blank form and render
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
                    max_subject_id = administration.objects.filter(study=study_obj).aggregate(Max('subject_id'))['subject_id__max'] # Find the subject ID with the largest number within this study. For example, a study with subject IDs like '3','5',and '25' would get a '25' in this field.
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

