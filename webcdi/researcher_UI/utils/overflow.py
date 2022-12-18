from researcher_UI.models import User, ip_address, study
from django.urls import reverse
from ipware.ip import get_client_ip

def overflow_fun(request, username, study_name):
    data = {}
    data["username"] = username  
    data["study_name"] = study_name  
    researcher = User.objects.get(
        username=username
    )  
    study_obj = study.objects.get(name=study_name, researcher=researcher)
    data["title"] = study_obj.instrument.verbose_name
    visitor_ip = str(get_client_ip(request))  
    prev_visitor = 0
    if visitor_ip and visitor_ip != "None":  
        prev_visitor = ip_address.objects.filter(
            ip_address=visitor_ip
        ).count()  
    if (
        prev_visitor > 0 and not request.user.is_authenticated
    ):  
        data[
            "repeat"
        ] = True  
    data["bypass_url"] = (
        reverse("administer_new_parent", args=[username, study_name]) + "?bypass=true"
    )
    return data
