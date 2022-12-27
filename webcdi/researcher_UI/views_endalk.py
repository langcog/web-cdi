from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .forms_endalk import *
from .models import researcher, study, administration
import json
from .mixins import StudyOwnerMixin
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from psycopg2.extras import NumericRange
from django.conf import settings
from django.core import serializers
from django.views import generic
from django.utils.translation import ugettext_lazy as _
from researcher_UI.utils.console_helper.post_helper import post_condition
from researcher_UI.utils.console_helper.get_helper import get_helper
from researcher_UI.utils.raw_gift_codes import raw_gift_code_fun
from researcher_UI.utils.add_study import add_study_fun
from researcher_UI.utils.add_paired_study import add_paired_study_fun
from researcher_UI.utils.admin_new import admin_new_fun
from researcher_UI.utils.admin_new_participant import admin_new_participant_fun
from researcher_UI.utils.admin_new_parent import admin_new_parent_fun
from researcher_UI.utils.overflow import overflow_fun
from researcher_UI.utils.import_data import import_data_fun


class Console(LoginRequiredMixin, generic.ListView):
    model = study
    template_name = "researcher_UI_endalk/interface.html"

    def get_context_data(self, *args, **kwargs):
        studies = study.objects.filter(
            researcher=self.request.user, active=True
        ).order_by("id")
        context = {"studies": studies}
        return context


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    """
    We used createView but we didn't extend form_valid method,
    Becuase We can't use form_class or get_form method.
    """

    model = study
    template_name = "researcher_UI_endalk/interface.html"

    def get_context_data(self, *args, **kwargs):
        num_per_page = 20
        context = get_helper(self.request, self.get_object().name, num_per_page)
        return context

    def post(self, request, *args, **kwargs):
        study_obj = self.get_object()
        permitted = study.objects.filter(
            researcher=request.user, name=study_obj.name
        ).exists()
        if permitted:
            study_obj = study.objects.get(researcher=request.user, name=study_obj.name)
            ids = request.POST.getlist("select_col")

            if all([x.isdigit() for x in ids]):
                """Check that the administration numbers are all numeric"""
                res = post_condition(request, ids, study_obj)
                return res


class RenameStudy(LoginRequiredMixin, generic.UpdateView):
    model = study
    template_name = "researcher_UI_endalk/rename_study_modal.html"
    form_class = RenameStudyForm

    def get_success_url(self):
        return reverse("researcher_ui:console_study", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(RenameStudy, self).get_context_data(**kwargs)
        study_obj = self.get_object()
        age_range = NumericRange(study_obj.min_age, study_obj.max_age)
        context["form_name"] = "Update Study"
        context["allow_payment"] = study_obj.allow_payment
        context["min_age"] = age_range.lower
        context["max_age"] = age_range.upper
        context["study_obj"] = study_obj
        return context

    def form_valid(self, form):
        raw_gift_codes = form.cleaned_data.get("gift_codes")
        raw_gift_amount = form.cleaned_data.get("gift_amount")
        raw_test_period = form.cleaned_data.get("test_period")
        new_study_name = form.cleaned_data.get("name")
        new_age_range = form.cleaned_data.get("age_range")
        study_obj = self.object

        if raw_test_period >= 1 and raw_test_period <= 28:
            study_obj.test_period = raw_test_period
        else:
            study_obj.test_period = 14

        study_obj.min_age = new_age_range.lower
        study_obj.max_age = new_age_range.upper
        study_obj.save()

        raw_gift_code_fun(raw_gift_amount, study_obj, new_study_name, raw_gift_codes)
        return super().form_valid(form)


class AddStudy(LoginRequiredMixin, generic.CreateView):
    template_name = "researcher_UI_endalk/add_study_modal.html"
    form_class = AddStudyForm

    def form_valid(self, form):
        study_instance = form.save(commit=False)
        study_name = form.cleaned_data.get("name")
        age_range = form.cleaned_data.get("age_range")
        study_instance.active = True
        researcher = self.request.user
        add_study_fun(study_instance, form, study_name, researcher, age_range)
        return redirect(reverse("researcher_ui:console"))

    def get_context_data(self, **kwargs):
        context = super(AddStudy, self).get_context_data(**kwargs)
        context["researcher"] = self.request.user
        return context


class AddPairedStudy(LoginRequiredMixin, generic.CreateView):
    model = study
    form_class = AddPairedStudyForm
    template_name = "researcher_UI_endalk/add_paired_study_modal.html"

    def form_valid(self, form):
        add_paired_study_fun(form, self.request.user)
        return redirect(reverse("researcher_ui:console"))

    def get_context_data(self, **kwargs):
        context = super(AddPairedStudy, self).get_context_data(**kwargs)
        researcher = self.request.user
        context["researcher"] = researcher
        return context


class AdminNew(LoginRequiredMixin, generic.UpdateView):
    model = study
    form_class = AdminNewForm
    template_name = "researcher_UI_endalk/administer_new_modal.html"

    def get_context_data(self, **kwargs):
        context = super(AdminNew, self).get_context_data(**kwargs)
        researcher = self.request.user
        study_obj = self.get_object()
        study_obj = study.objects.get(researcher=researcher, name=study_obj.name)
        context["username"] = researcher.username
        context["study_name"] = study_obj.name
        context["study_group"] = study_obj.study_group
        context["object"] = study_obj
        return context

    def form_valid(self, form, *args, **kwargs):
        researcher = self.request.user
        study_obj = self.get_object()
        permitted = study.objects.filter(
            researcher=researcher, name=study_obj.name
        ).exists()

        study_obj = study.objects.get(researcher=researcher, name=study_obj.name)
        data = admin_new_fun(self.request, permitted, study_obj.name, study_obj)
        return HttpResponse(json.dumps(data), content_type="application/json")


class AdministerNewParticipant(LoginRequiredMixin, generic.CreateView):
    def post(self, request, username, study_name):
        admin = admin_new_participant_fun(request, username, study_name)
        return redirect(reverse("administer_cdi_form", args=[admin.url_hash]))


class AdminNewParent(LoginRequiredMixin, generic.View):
    def get(self, request, username, study_name):
        study_obj, let_through, bypass, source_id = admin_new_parent_fun(
            request, username, study_name
        )
        if let_through:
            if study_obj.instrument.form in settings.CAT_FORMS:
                return redirect(
                    reverse(
                        "cat_forms:create-new-background-info",
                        kwargs={
                            "study_id": study_obj.id,
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
                            "study_id": study_obj.id,
                            "bypass": bypass,
                            "source_id": source_id,
                        },
                    )
                )
        else:
            redirect_url = reverse("overflow", args=[username, study_name])
        return redirect(redirect_url)


class Overflow(LoginRequiredMixin, generic.View):
    """
    TODO
    I wanted to change to detailview, but I couldn't find the page to test after doing that.
    """

    def get(self, request, username, study_name):
        data = overflow_fun(request, username, study_name)
        return render(request, "cdi_forms/overflow.html", data)


class ImportData(LoginRequiredMixin, generic.UpdateView):
    model = study
    form_class = ImportDataForm
    template_name = "researcher_UI_endalk/import_data.html"

    def form_valid(self, form):
        data = import_data_fun(self.request, self.get_object())
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(ImportData, self).get_context_data(**kwargs)
        study_obj = self.get_object()
        context["form"] = ImportDataForm(researcher=self.request.user, study=study_obj)
        return context


class EditStudyView(LoginRequiredMixin, StudyOwnerMixin, generic.UpdateView):
    model = administration
    form_class = StudyFormForm
    template_name = "researcher_UI_endalk/interface.html"

    def get_context_data(self, **kwargs):
        context = get_helper(self.request, self.object.study.name, 20)
        context["study"] = self.object.study
        return context

    def form_valid(self, form):
        obj = self.get_object()
        if "subject_id" in form.changed_data:
            obj.subject_id = form.cleaned_data["subject_id"]
            count = administration.objects.filter(
                study_id=obj.study.pk, subject_id=form.cleaned_data["subject_id"]
            ).count()
            if count > 1:
                return JsonResponse(
                    {"error": "subject id is already existed."}, status=400
                )
        if "local_lab_id" in form.changed_data:
            obj.local_lab_id = form.cleaned_data["local_lab_id"]
        if "opt_out" in form.changed_data:
            obj.opt_out = form.cleaned_data["opt_out"]

        obj.save()

        return JsonResponse(
            {"message": "Your data is updated successfully"}, status=200
        )


class AjaxDemographicForms(generic.DetailView):
    def get(self, request):
        pk = request.GET["id"]
        data = serializers.serialize(
            "json",
            instrument.objects.get(name=pk).demographics.all().order_by("pk"),
            fields=("id", "name"),
        )
        return HttpResponse(data, content_type="application/json")


class ResearcherAddInstruments(LoginRequiredMixin, UpdateView):
    model = researcher
    form_class = AddInstrumentForm
    template_name = "researcher_UI_endalk/researcher_form.html"

    def get_success_url(self):
        return reverse("researcher_ui:console")
