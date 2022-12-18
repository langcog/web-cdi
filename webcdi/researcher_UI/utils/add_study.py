from researcher_UI.models import study

def add_study_fun(study_instance, form, study_name, researcher, age_range):
    data = {}
    try:
        study_instance.min_age = age_range.lower
        study_instance.max_age = age_range.upper
    except:
        study_instance.min_age = study_instance.instrument.min_age
        study_instance.max_age = study_instance.instrument.max_age

    slash_in_name = True if "/" in study_name else None
    not_unique_name = (
        True
        if study.objects.filter(researcher=researcher, name=study_name).exists()
        else None
    )

    study_instance.researcher = researcher
    print(form.cleaned_data)
    if not form.cleaned_data.get("test_period"):
            study_instance.test_period = 14

    if not slash_in_name and not not_unique_name: 
        study_instance.save() 
        data["stat"] = "ok"
        data["redirect_url"] = "/endalk/study/" + study_name + "/"

    elif not_unique_name: 
        data["stat"] = "error"
        data["error_message"] = "Study already exists; Use a unique name"

    elif slash_in_name:
        data["stat"] = "error"
        data[
            "error_message"
        ] = "Study name has a forward slash ('/') inside. Please remove or replace this character."
    print(data)
    return data
