import datetime
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import models
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, UpdateView
from ipware.ip import get_client_ip

from cdi_forms.models import BackgroundInfo
from researcher_UI.forms import StudyFormForm
from researcher_UI.mixins import StudyOwnerMixin
from researcher_UI.models import Administration, Study, ip_address
from researcher_UI.utils import (admin_new_participant_fun, max_repeat_num,
                                 max_subject_id, random_url_generator)
from researcher_UI.utils.console_helper import get_helper


class EditAdministrationView(LoginRequiredMixin, StudyOwnerMixin, UpdateView):
    model = Administration
    form_class = StudyFormForm
    template_name = "researcher_UI/interface.html"

    def get_context_data(self, **kwargs):
        context = get_helper(self.request, self.object.study.name, 20)
        context["study"] = self.object.study
        return context

    def form_valid(self, form):
        obj = self.get_object()

        if "subject_id" in form.changed_data:
            count = Administration.objects.filter(
                study_id=obj.study.pk, subject_id=form.cleaned_data["subject_id"]
            ).count()

            if count > 1:
                return JsonResponse(
                    {"error": "subject id is already existed."}, status=400
                )

            _instances = Administration.objects.filter(
                study=obj.study, subject_id=form.cleaned_data["subject_id_old"]
            )

            new_subject_id = int(form.cleaned_data["subject_id"])

            for _instance in _instances:
                _instance.subject_id = new_subject_id
                _instance.save()

        if "local_lab_id" in form.changed_data:
            obj.local_lab_id = form.cleaned_data["local_lab_id"]
            obj.save()
        if "opt_out" in form.changed_data:
            obj.opt_out = form.cleaned_data["opt_out"]
            obj.save()

        super().form_valid(form)
        return JsonResponse(
            {"message": "Your data is updated successfully"}, status=200
        )


class AddNewParent(DetailView):
    model = Study

    def admin_new_parent_fun(self, request):
        if "source_id" in request.GET:
            source_id = request.GET["source_id"]
        else:
            source_id = None
        if "child" in request.GET and "response" in request.GET:
            source_id = f"{request.GET['child']}_{request.GET['response']}"

        subject_cap = self.object.subject_cap
        completed_admins = Administration.objects.filter(
            study=self.object, completed=True
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

        return let_through, bypass, source_id

    def get_object(self) -> models.Model:
        researcher = User.objects.get(username=self.kwargs["username"])
        self.object = Study.objects.get(
            name=self.kwargs["study_name"], researcher=researcher
        )
        return self.object

    def get(self, request, username, study_name):
        self.get_object()
        let_through, bypass, source_id = self.admin_new_parent_fun(request)
        if let_through:
            if self.object.no_demographic_boolean:
                event_id = (
                    None if not "event_id" in request.GET else request.GET["event_id"]
                )
                if BackgroundInfo.objects.filter(
                    source_id=request.GET["source_id"],
                    event_id=event_id,
                    administration__study=self.object,
                ).exists():
                    background_info = BackgroundInfo.objects.get(
                        source_id=request.GET["source_id"],
                        event_id=event_id,
                        administration__study=self.object,
                    )
                    return redirect(
                        "administer_cdi_form",
                        hash_id=background_info.administration.url_hash,
                    )

                if (
                    not "source_id" in request.GET
                    or not "age" in request.GET
                    or not "sex" in request.GET
                ):
                    raise Http404(
                        "Age, sex and source_id must be included in the a no demographic call."
                    )

                if BackgroundInfo.objects.filter(
                    source_id=request.GET["source_id"],
                    administration__study=self.object,
                ).exists():
                    old_admin = BackgroundInfo.objects.filter(
                        source_id=request.GET["source_id"],
                        administration__study=self.object,
                    )[0].administration
                    new_admin = Administration.objects.create(
                        study=self.object,
                        subject_id=old_admin.subject_id,
                        repeat_num=max_repeat_num(old_admin) + 1,
                        url_hash=random_url_generator(),
                        completed=False,
                        due_date=timezone.now()
                        + datetime.timedelta(days=self.object.test_period),
                    )
                else:
                    new_admin = Administration.objects.create(
                        study=self.object,
                        subject_id=max_subject_id(self.object) + 1,
                        repeat_num=1,
                        url_hash=random_url_generator(),
                        completed=False,
                        due_date=timezone.now()
                        + datetime.timedelta(days=self.object.test_period),
                    )

                if "offset" in request.GET:
                    offset = int(request.GET["offset"])
                else:
                    offset = 0
                data = {}
                if offset == 0:
                    born_on_due_date = 0
                    due_date_diff = 0
                    early_or_late = None
                else:
                    born_on_due_date = 1
                    due_date_diff = abs(offset)
                    if offset < 0:
                        early_or_late = "early"
                    else:
                        early_or_late = "late"

                new_background = BackgroundInfo.objects.create(
                    administration=new_admin,
                    sex=request.GET["sex"].upper(),
                    source_id=request.GET["source_id"],
                    event_id=event_id,
                    age=int(request.GET["age"]),
                    born_on_due_date=born_on_due_date,
                    due_date_diff=due_date_diff,
                    early_or_late=early_or_late,
                )
                new_admin.completedBackgroundInfo = True
                new_admin.save()
                return redirect("administer_cdi_form", hash_id=new_admin.url_hash)

            if self.object.instrument.form in settings.CAT_FORMS:
                return redirect(
                    reverse(
                        "cat_forms:create-new-background-info",
                        kwargs={
                            "study_id": self.object.id,
                            "bypass": bypass,
                            "source_id": source_id,
                        },
                    )
                )
            else:
                return redirect(
                    reverse(
                        "create-new-background-info",
                        kwargs={
                            "study_id": self.object.id,
                            "bypass": bypass,
                            "source_id": source_id,
                        },
                    )
                )
        else:
            redirect_url = reverse("researcher_ui:overflow", args=[self.object.id])
        return redirect(redirect_url)
