from django.views.generic import UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib import messages

from psycopg2.extras import NumericRange

from researcher_UI.utils import raw_gift_code_fun, add_paired_study_fun
from researcher_UI.models import study
from researcher_UI.forms import AddStudyForm, AddPairedStudyForm, EditStudyForm
from researcher_UI.mixins import ReseacherOwnsStudyMixin


class AddPairedStudy(LoginRequiredMixin, CreateView):
    model = study
    form_class = AddPairedStudyForm
    template_name = "researcher_UI/add_paired_study_modal.html"

    def form_valid(self, form):
        add_paired_study_fun(form, self.request.user)
        return redirect(reverse("researcher_ui:console"))

    def get_context_data(self, **kwargs):
        context = super(AddPairedStudy, self).get_context_data(**kwargs)
        researcher = self.request.user
        context["researcher"] = researcher
        return context


class UpdateStudyView(LoginRequiredMixin, ReseacherOwnsStudyMixin, UpdateView):
    model = study
    template_name = "researcher_UI/study_form.html"
    form_class = EditStudyForm

    def get_success_url(self):
        return reverse("researcher_ui:console_study", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        age_range = NumericRange(self.object.min_age, self.object.max_age)
        context["form_name"] = "Update Study"
        context["allow_payment"] = self.object.allow_payment
        context["min_age"] = age_range.lower
        context["max_age"] = age_range.upper
        context["study_obj"] = self.object
        return context

    def form_valid(self, form):
        raw_gift_codes = form.cleaned_data.get("gift_codes")
        raw_gift_amount = form.cleaned_data.get("gift_amount")
        raw_test_period = form.cleaned_data.get("test_period")
        new_study_name = form.cleaned_data.get("name")

        if raw_test_period >= 1 and raw_test_period <= 1095:
            self.object.test_period = raw_test_period
        else:
            self.object.test_period = 14

        self.object.active = True
        self.object.researcher = self.request.user
        self.object.save()

        res = raw_gift_code_fun(
            raw_gift_amount, self.object, new_study_name, raw_gift_codes
        )
        if res["stat"] == "ok" and raw_gift_amount:
            messages.success(
                self.request,
                mark_safe(
                    f"The following gift codes of value {raw_gift_amount} have been added: {raw_gift_codes}"
                ),
            )
        elif res["stat"] == "error":
            messages.error(
                self.request,
                mark_safe(
                    f'There was an error with the gift codes.  None were added.  The error message is: {res["error_message"]}'
                ),
            )
        return super().form_valid(form)


class AddStudy(LoginRequiredMixin, CreateView):
    template_name = "researcher_UI/study_form.html"
    model = study
    form_class = AddStudyForm

    def get_form(self):
        self.request.user.refresh_from_db()
        form_class = AddStudyForm(
            self.request.POST or None, researcher=self.request.user
        )
        return form_class

    def form_valid(self, form):
        study_instance = form.save(commit=False)
        age_range = form.cleaned_data.get("age_range")
        study_instance.active = True
        researcher = self.request.user

        try:
            study_instance.min_age = age_range.lower
            study_instance.max_age = age_range.upper
        except:
            study_instance.min_age = study_instance.instrument.min_age
            study_instance.max_age = study_instance.instrument.max_age

        study_instance.researcher = researcher
        if not form.cleaned_data.get("test_period"):
            study_instance.test_period = 14

        study_instance.save()

        return redirect(
            reverse("researcher_ui:console_study", args=(study_instance.pk,))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["researcher"] = self.request.user
        return context