from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
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


class Console(LoginRequiredMixin, generic.View):
    def post(self, request, study_name=None):
        permitted = study.objects.filter(
            researcher=request.user, name=study_name
        ).exists()
        if permitted:
            study_obj = study.objects.get(researcher=request.user, name=study_name)
            ids = request.POST.getlist("select_col")
            if all([x.isdigit() for x in ids]):
                """Check that the administration numbers are all numeric"""
                res =  post_condition(request, ids, study_obj)
                if res == None:
                    context = get_helper(request, study_name, 20)
                    return render(request, "researcher_UI_endalk/interface.html", context)
                return res
        
    def get(self, request, study_name=None, num_per_page=20):
        context = get_helper(request, study_name, num_per_page)
        return render(request, "researcher_UI_endalk/interface.html", context)


class RenameStudy(LoginRequiredMixin, generic.View):
    def get(self, request, study_name):
        form_package = {}
        study_obj = study.objects.get(researcher=request.user, name=study_name)
        age_range = NumericRange(study_obj.min_age, study_obj.max_age)
        form = RenameStudyForm(
            instance=study_obj, old_study_name=study_obj.name, age_range=age_range
        )
        form_package["form"] = form
        form_package["form_name"] = "Update Study"
        form_package["allow_payment"] = study_obj.allow_payment
        form_package["min_age"] = age_range.lower
        form_package["max_age"] = age_range.upper
        form_package["study_obj"] = study_obj
        return render(request, "researcher_UI_endalk/rename_study_modal.html", form_package)

    def post(self, request, study_name):
        data = {}
        form_package = {}
        raw_gift_codes = None

        study_obj = study.objects.get(researcher=request.user, name=study_name)
        age_range = NumericRange(study_obj.min_age, study_obj.max_age)
        form = RenameStudyForm(
            study_name, request.POST, instance=study_obj, age_range=age_range
        )

        if form.is_valid():
            researcher = request.user
            new_study_name = form.cleaned_data.get("name")
            raw_gift_codes = form.cleaned_data.get("gift_codes")
            raw_gift_amount = form.cleaned_data.get("gift_amount")
            raw_test_period = form.cleaned_data.get("test_period")
            new_age_range = form.cleaned_data.get("age_range")
            study_obj.min_age = new_age_range.lower
            study_obj.max_age = new_age_range.upper
            study_obj = form.save(commit=False)

            if raw_test_period >= 1 and raw_test_period <= 28:
                study_obj.test_period = raw_test_period
            else:
                study_obj.test_period = 14

            if new_study_name != study_name:
                is_existed = study.objects.filter(
                    researcher=researcher, name=new_study_name
                ).exists()

                if is_existed or "/" in new_study_name:
                    study_obj.name = study_name

            study_obj.save()
            new_study_name = study_obj.name
            data = raw_gift_code_fun(
                raw_gift_amount, study_obj, new_study_name, raw_gift_codes
            )
            return redirect('console', study_name=study_name)

        else:
            data["stat"] = "re-render"
            form_package["form"] = form
            form_package["form_name"] = "Update Study"
            form_package["allow_payment"] = study_obj.allow_payment
            return render(request, "researcher_UI_endalk/rename_study_modal.html", form_package)


class AddStudy(LoginRequiredMixin, generic.View):
    def post(self, request):
        data = {}
        researcher = request.user
        form = AddStudyForm(request.POST, researcher=researcher)
        if form.is_valid():
            study_instance = form.save(commit=False)
            study_name = form.cleaned_data.get("name")
            age_range = form.cleaned_data.get("age_range")
            study_instance.active = True
            data = add_study_fun(
                study_instance, form, study_name, researcher, age_range
            )
            return redirect('console', study_name=study_name)
        else:
            data["stat"] = "re-render"
            form_package = {}
            form_package["form"] = form
            form_package["form_name"] = "Add New Study"
            return render(request, "researcher_UI_endalk/add_study_modal.html", form_package)

    def get(self, request):
        researcher = request.user
        form = AddStudyForm(researcher=researcher)
        form_package = {}
        form_package["form"] = form
        form_package["form_name"] = "Add New Study"
        return render(request, "researcher_UI_endalk/add_study_modal.html", form_package)


class AddPairedStudy(LoginRequiredMixin, generic.View):
    def post(self, request):
        data = {}
        researcher = request.user
        form = AddPairedStudyForm(request.POST)
        if form.is_valid():
            data = add_paired_study_fun(form, researcher)
            return redirect('console')
        else:
            data["stat"] = "re-render"
            return render(
                request, "researcher_UI_endalk/add_paired_study_modal.html", {"form": form}
            )

    def get(self, request):
        researcher = request.user
        form = AddPairedStudyForm(researcher=researcher)
        return render(
            request, "researcher_UI_endalk/add_paired_study_modal.html", {"form": form}
        )


class AdminNew(LoginRequiredMixin,generic.View):
    def post(self, request, study_name):
        permitted = study.objects.filter(
            researcher=request.user, name=study_name
        ).exists()
        study_obj = study.objects.get(researcher=request.user, name=study_name)
        data = admin_new_fun(request, permitted, study_name, study_obj)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get(self, request, study_name):
        context = {}
        study_obj = study.objects.get(researcher=request.user, name=study_name)
        context["username"] = request.user.username
        context["study_name"] = study_name
        context["study_group"] = study_obj.study_group
        context["object"] = study_obj
        return render(request, "researcher_UI_endalk/administer_new_modal.html", context)


class AdministerNewParticipant(LoginRequiredMixin,generic.View):
    def post(self, request, username, study_name):
        admin = admin_new_participant_fun(request, username, study_name)
        return redirect(reverse("administer_cdi_form", args=[admin.url_hash]))


class AdminNewParent(LoginRequiredMixin,generic.View):
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


class Overflow(LoginRequiredMixin,generic.View):
    def get(self, request, username, study_name):
        data = overflow_fun(request, username, study_name)
        return render(request, "cdi_forms/overflow.html", data)


class ImportData(LoginRequiredMixin,generic.View):
    def post(self, request, study_name):
        data = {}
        study_obj = study.objects.get(researcher=request.user, name=study_name)
        form = ImportDataForm(
            request.POST, request.FILES, researcher=request.user, study=study_obj
        )
        if form.is_valid():
            data = import_data_fun(request, study_obj)
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            data["stat"] = "re-render"
            return render(request, "researcher_UI_endalk/import_data.html", {"form": form})

    def get(self, request, study_name):
        study_obj = study.objects.get(researcher=request.user, name=study_name)
        form = ImportDataForm(researcher=request.user, study=study_obj)
        return render(request, "researcher_UI_endalk/import_data.html", {"form": form})


class EditAdministrationView(LoginRequiredMixin, StudyOwnerMixin, UpdateView):
    model = administration
    form_class = EditSubjectIDForm
    old_subject_id = None

    def get_success_url(self):
        return reverse("console", kwargs={"study_name": self.object.study.name})

    def get_context_data(self, **kwargs):
        ctx = super(EditAdministrationView, self).get_context_data(**kwargs)
        self.study = ctx["study"] = self.object.study
        return ctx

    def post(self, request, *args, **kwargs):
        form = EditSubjectIDForm(self.request.POST)
        if form.is_valid():
            self.old_subject_id = self.get_object().subject_id
        return super(EditAdministrationView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        instances = administration.objects.filter(
            study=self.object.study, subject_id=self.old_subject_id
        )
        new_subject_id = int(self.request.POST["subject_id"])
        for instance in instances:
            instance.subject_id = new_subject_id
            instance.save()
        return super(EditAdministrationView, self).form_valid(form)


class EditLocalLabIdView(LoginRequiredMixin, StudyOwnerMixin, UpdateView):
    model = administration
    form_class = EditLocalLabIDForm

    def get_success_url(self):
        return reverse("console", kwargs={"study_name": self.object.study.name})

    def get_context_data(self, **kwargs):
        ctx = super(EditLocalLabIdView, self).get_context_data(**kwargs)
        self.study = ctx["study"] = self.object.study
        return ctx

class EditLocalLabIdView(LoginRequiredMixin, StudyOwnerMixin, UpdateView):
    model = administration
    form_class = EditLocalLabIDForm

    def get_success_url(self):
        return reverse("console", kwargs={"study_name": self.object.study.name})

    def get_context_data(self, **kwargs):
        ctx = super(EditLocalLabIdView, self).get_context_data(**kwargs)
        self.study = ctx["study"] = self.object.study
        return ctx


class EditStudyView(LoginRequiredMixin, generic.UpdateView):
    model = administration
    form_class = StudyFormForm


    def get_context_data(self, **kwargs):
        ctx = super(EditStudyView, self).get_context_data(**kwargs)
        self.study = ctx["study"] = self.object.study
        return ctx

    def form_valid(self, form):
        form.save()
        context = get_helper(self.request,  self.object.study.name, 20)
        return render(self.request, "researcher_UI_endalk/interface.html", context)

    def get(self, request, pk):
        obj = administration.objects.get(pk=pk)
        context = get_helper(self.request,  obj.study.name, 20)
        return render(self.request, "researcher_UI_endalk/interface.html", context)

class EditOptOutView(LoginRequiredMixin, StudyOwnerMixin, UpdateView):
    model = administration
    form_class = EditOptOutForm

    def get_success_url(self):
        return reverse("console", kwargs={"study_name": self.object.study.name})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.study = ctx["study"] = self.object.study
        return ctx


class AjaxDemographicForms(generic.View):
    def get(self, request):
        pk = request.GET["id"]
        data = serializers.serialize(
            "json",
            instrument.objects.get(name=pk).demographics.all().order_by("pk"),
            fields=("id", "name"),
        )
        return HttpResponse(data, content_type="application/json")


class ResearcherAddInstruments(UpdateView):
    model = researcher
    form_class = AddInstrumentForm
    template_name = "researcher_UI_endalk/researcher_form.html"

    def get_success_url(self) -> str:
        return reverse("console")
