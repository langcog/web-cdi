from researcher_UI.utils import random_url_generator
from researcher_UI.models import User, Study, ip_address, Administration
from ipware.ip import get_client_ip
import requests
from django.utils import timezone
import datetime



def admin_new_participant_fun(request, username, study_name):
    researcher = User.objects.get(username=username)
    study_obj = Study.objects.get(name=study_name, researcher=researcher)
    subject_cap = study_obj.subject_cap
    test_period = int(study_obj.test_period)
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

    if (prev_visitor < 5 and completed < 5) or request.user.is_authenticated:
        if completed_admins < subject_cap:
            let_through = True
        elif subject_cap is None:
            let_through = True
        elif bypass:
            let_through = True

    if let_through:
        subject_id_obscured = request.GET.get("id")
        sid1 = subject_id_obscured[11:].split("827483249828")[0]
        sid2 = subject_id_obscured[11:].split("827483249828")[1].split("9248232436")[0]
        if sid1 != sid2:
            return
        subject_id = sid1
        if subject_id:
            num_admins = Administration.objects.filter(
                study=study_obj, subject_id=subject_id
            ).count()
            if num_admins == 0:
                requests.post(
                    "https://wordful-flask.herokuapp.com/addEmailAddressToStudy",
                    json={
                        "email": request.GET.get("email"),
                        "studyId": "ContinuousCDI",
                    },
                )
                admin = administration(
                    study=study_obj, subject_id=subject_id, repeat_num=1
                )
                admin.url_hash = random_url_generator()
                admin.completed = False
                admin.due_date = timezone.now() + datetime.timedelta(days=test_period)
                admin.bypass = None
                admin.save()
                
            elif num_admins == 1:
                if request.GET.get("final_cdi"):
                    admin = Administration.objects.create(
                        study=study_obj,
                        subject_id=subject_id,
                        repeat_num=2,
                        url_hash=random_url_generator(),
                        completed=False,
                        due_date=datetime.datetime.now() + datetime.timedelta(days=14),
                    )
                else:
                    admin = Administration.objects.get(
                        study=study_obj, subject_id=subject_id, repeat_num=1
                    )
            else:
                admin = Administration.objects.get(
                    study=study_obj, subject_id=subject_id, repeat_num=2
                )
            return admin
