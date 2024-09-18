import json
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from ipware.ip import get_client_ip

from researcher_UI.forms import *
from researcher_UI.models import Study
from researcher_UI.utils.admin_new import admin_new_fun
from researcher_UI.utils.console_helper.get_helper import get_helper
from researcher_UI.utils.console_helper.post_helper import post_condition


class Console(LoginRequiredMixin, generic.ListView):
    model = Study
    template_name = "researcher_UI/interface.html"

    def get_context_data(self, *args, **kwargs):
        studies = Study.objects.filter(
            researcher=self.request.user, active=True
        ).order_by("id")
        context = {"studies": studies}
        return context


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    """
    We used createView but we didn't extend form_valid method,
    Becuase We can't use form_class or get_form method.
    """

    model = Study
    template_name = "researcher_UI/interface.html"

    def get_context_data(self, *args, **kwargs):
        num_per_page = 20
        context = get_helper(self.request, self.get_object().name, num_per_page)
        return context

    def post(self, request, *args, **kwargs):
        logger.debug(f"request.POST is {request.POST}")
        study_obj = self.get_object()
        permitted = Study.objects.filter(
            researcher=request.user, name=study_obj.name
        ).exists()
        if permitted:
            study_obj = Study.objects.get(researcher=request.user, name=study_obj.name)
            ids = request.POST.getlist("select_col")

            if all([x.isdigit() for x in ids]):
                """Check that the administration numbers are all numeric"""
                # try:
                res = post_condition(request, ids, study_obj)
                # except Exception as e:
                #    context = {"error": "This combination is already existed."}
                #    return render(request, "researcher_UI/500_error.html", context)
                logger.debug(f"res is {res}")
                if res:
                    return res
                else:
                    target = reverse(
                        "researcher_ui:console_study", kwargs={"pk": study_obj.pk}
                    )
                    return redirect(f'{target}?search={request.POST["search"]}')
            else:
                target = reverse(
                    "researcher_ui:console_study", kwargs={"pk": study_obj.pk}
                )
                return redirect(f'{target}?search={request.POST["search"]}')


class AdminNew(LoginRequiredMixin, generic.UpdateView):
    model = Study
    form_class = AdminNewForm
    # template_name = "researcher_UI/administer_new_modal.html"

    def dispatch(self, request, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        # check if valid code if chargeable
        if not self.object.valid_code(self.request.user):
            return ["researcher_UI/no_brookes_code.html"]
        else:
            return ["researcher_UI/administer_new_modal.html"]

    def get_context_data(self, **kwargs):
        context = super(AdminNew, self).get_context_data(**kwargs)
        researcher = self.request.user
        context["username"] = researcher.username
        context["study_name"] = self.object.name
        context["study_group"] = self.object.study_group
        return context

    def form_valid(self, form, *args, **kwargs):
        researcher = self.request.user
        permitted = Study.objects.filter(
            researcher=researcher, name=self.object.name
        ).exists()

        data = admin_new_fun(self.request, permitted, self.object.name, self.object)
        return HttpResponse(json.dumps(data), content_type="application/json")


class Overflow(generic.DetailView):
    model = Study
    template_name = "cdi_forms/overflow.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)

        visitor_ip = str(get_client_ip(self.request))
        prev_visitor = 0
        if visitor_ip and visitor_ip != "None":
            prev_visitor = ip_address.objects.filter(ip_address=visitor_ip).count()
        if prev_visitor > 0 and not self.request.user.is_authenticated:
            ctx["repeat"] = True
        ctx["bypass_url"] = (
            reverse(
                "researcher_ui:administer_new_parent",
                args=[self.object.researcher.username, self.object.name],
            )
            + "?bypass=true"
        )
        return ctx
