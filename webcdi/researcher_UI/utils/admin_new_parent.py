from django.contrib.auth.models import User
from ipware.ip import get_client_ip

from researcher_UI.models import Administration, Study, ip_address


def admin_new_parent_fun(request, username, study_name):
    if "source_id" in request.GET:
        source_id = request.GET["source_id"]
    else:
        source_id = None
    if "child" in request.GET and "response" in request.GET:
        source_id = f"{request.GET['child']}_{request.GET['response']}"

    researcher = User.objects.get(username=username)
    study_obj = Study.objects.get(name=study_name, researcher=researcher)
    subject_cap = study_obj.subject_cap
    completed_admins = Administration.objects.filter(
        study=study_obj, completed=True
    ).count()
    bypass = request.GET.get("bypass", None)
    let_through = None
    prev_visitor = 0
    visitor_ip = str(get_client_ip(request))
    completed = int(request.get_signed_cookie("completed_num", "0"))
    if visitor_ip:
        prev_visitor = ip_address.objects.filter(ip_address=visitor_ip).count()

    if (prev_visitor < 1 and completed < 2) or request.user.is_authenticated:
        if subject_cap is None:
            let_through = True
        elif completed_admins < subject_cap:
            let_through = True
        elif bypass:
            let_through = True

    return study_obj, let_through, bypass, source_id
