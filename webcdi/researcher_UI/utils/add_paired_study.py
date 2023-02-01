from researcher_UI.models import study


def add_paired_study_fun(form, researcher):
    data = {}
    study_group = form.cleaned_data.get("study_group")
    paired_studies = form.cleaned_data.get("paired_studies")
    permissions = []
    for one_study in paired_studies:
        permitted = study.objects.filter(researcher=researcher, name=one_study).exists()
        permissions.append(permitted)
        if permitted:
            study_obj = study.objects.get(researcher=researcher, name=one_study)
            study_obj.study_group = study_group
            study_obj.save()

    if all(True for permission in permissions):
        data["stat"] = "ok"
        data["redirect_url"] = "/endalk/"

    else:
        data["stat"] = "error"
        data["error_message"] = "Study group already exists; Use a unique name"
    return data
