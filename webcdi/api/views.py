import json

import numpy as np
import pandas as pd
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from api.mixins import StudyOwnerMixin
from cdi_forms.models import BackgroundInfo, Instrument_Forms
from cdi_forms.views import get_model_header
from researcher_UI.models import (Administration, InstrumentScore, Study,
                                  administration_data)
from researcher_UI.utils import (format_admin_data, format_admin_header,
                                 get_background_header, get_score_headers,
                                 get_study_scores)


@method_decorator(csrf_exempt, name="dispatch")
class BaseAPIView(StudyOwnerMixin, TemplateView):
    http_method_names = [
        "post",
    ]

    def get_json(self, request, study_obj, administrations=None):
        adjusted = True
        administrations = (
            administrations
            if administrations is not None
            else Administration.objects.filter(study=study_obj)
        )
        if not administrations.filter(completed=True).exists():
            return json.dumps({"Error": "You must select at least 1 completed survey"})
        model_header = get_model_header(study_obj.instrument.name)

        # Fetch administration variables
        admin_header = format_admin_header(study_obj)

        # Fetch background data variables
        background_header = get_background_header(study_obj)

        try:
            answers = administration_data.objects.values(
                "administration_id", "item_ID", "value"
            ).filter(administration_id__in=administrations)
            melted_answers = pd.DataFrame.from_records(answers).pivot(
                index="administration_id", columns="item_ID", values="value"
            )
            melted_answers.reset_index(level=0, inplace=True)
        except:
            melted_answers = pd.DataFrame(
                columns=get_model_header(study_obj.instrument.name)
            )

        new_headers = (
            Instrument_Forms.objects.values("itemID", "item")
            .filter(instrument=study_obj.instrument)
            .distinct()
        )
        new_headers = {x["itemID"]: x["item"] for x in new_headers}
        model_header = [new_headers.get(n, n) for n in model_header]

        melted_answers.rename(columns=new_headers, inplace=True)

        background_data = BackgroundInfo.objects.values().filter(
            administration__in=administrations
        )

        BI_choices = {}

        fields = BackgroundInfo._meta.get_fields()
        for field in fields:
            if field.choices:
                field_choices = dict(field.choices)
                for k, v in list(field_choices.items()):
                    if str(k) == str(v):
                        field_choices.pop(k, None)
                BI_choices[field.name] = {
                    str(k): str(v) for k, v in field_choices.items()
                }

        new_background = (
            pd.DataFrame.from_records(background_data).astype(str).replace(BI_choices)
        )
        try:
            new_background["administration_id"] = new_background[
                "administration_id"
            ].astype("int64")
        except Exception as e:
            messages.add_message(
                request,
                messages.ERROR,
                f"System error {e}.  You must select at least 1 completed response",
            )
            return render(request, "error-page.html")

        # Add scoring
        melted_scores = get_study_scores(administrations)
        if len(melted_scores) < 1:
            return json.dumps(
                {"Error": f"There are no data in the study(ies) to report"}
            )
        score_header = get_score_headers(study_obj, adjusted=adjusted)
        melted_scores.set_index("administration_id")
        missing_columns = list(set(score_header) - set(melted_scores.columns))
        if missing_columns:
            melted_scores = melted_scores.reindex(
                columns=np.append(melted_scores.columns.values, missing_columns)
            )

        for instance in InstrumentScore.objects.filter(instrument=study_obj.instrument):
            if instance.kind == "count":
                melted_scores[instance.title].replace(
                    r"^\s*$", 0, regex=True, inplace=True
                )
                melted_scores[instance.title].replace(np.NaN, 0, inplace=True)

        try:
            background_answers1 = pd.merge(
                new_background, melted_answers, how="outer", on="administration_id"
            )
            background_answers = pd.merge(
                background_answers1, melted_scores, how="outer", on="administration_id"
            )
        except:
            background_answers = pd.DataFrame(
                columns=list(new_background)
                + list(melted_answers)
                + list(melted_scores)
            )

        # Try to format administration data for pandas dataframe
        admin_data = format_admin_data(pd, study_obj, administrations, admin_header)

        try:
            combined_data = pd.merge(
                admin_data, background_answers, how="outer", on="administration_id"
            )
        except Exception as e:
            messages.add_message(
                request,
                messages.ERROR,
                f"System error {e}:   You must select at least 1 completed response",
            )
            return render(request, "error-page.html")

        # Recreate link for administration
        test_url = "".join(
            [
                "http://",
                get_current_site(request).domain,
                reverse("administer_cdi_form", args=["a" * 64]),
            ]
        ).replace("a" * 64 + "/", "")
        combined_data["link"] = test_url + combined_data["link"]

        s2 = combined_data.columns.to_series()
        combined_data.columns = combined_data.columns + s2.groupby(
            s2
        ).cumcount().astype(str).radd("_").str.replace("_0", "")

        missing_columns = list(set(model_header) - set(combined_data.columns))
        if missing_columns:
            combined_data = combined_data.reindex(
                columns=np.append(combined_data.columns.values, missing_columns)
            )

        # Organize columns
        combined_data = combined_data[
            admin_header + background_header + model_header + score_header
        ]

        combined_data = combined_data.replace("nan", "", regex=True)
        combined_data = combined_data.replace("None", "", regex=True)
        combined_data["child_ethnicity"].replace("[]", "", inplace=True)
        combined_data["other_languages"].replace("[]", "", inplace=True)

        # add footer
        if study_obj.instrument.language in [
            "English"
        ] and study_obj.instrument.form in [
            "WS",
            "WG",
        ]:
            pd.concat(
                [
                    combined_data,
                    pd.DataFrame(
                        [{"study_name": "3rd Edition (Marchman et al., 2023)"}]
                    ),
                ],
                ignore_index=True,
            )

        # Turn pandas dataframe into a CSV
        return combined_data.transpose().to_json()


class StudyAPI(BaseAPIView):
    def post(self, request, *args, **kwargs):
        study_obj = Study.objects.get(pk=kwargs.pop("pk"))
        qs_json = self.get_json(request, study_obj)

        # Return CSV
        return HttpResponse(qs_json, content_type="application/json")


class SourceAPI(BaseAPIView):
    def post(self, request, *args, **kwargs):
        study = Study.objects.get(pk=kwargs.pop("pk"))
        if "event_id" in kwargs:
            administrations = Administration.objects.filter(
                backgroundinfo__in=BackgroundInfo.objects.filter(
                    event_id=kwargs.pop("event_id"), source_id=kwargs.pop("source_id")
                )
            )
        else:
            administrations = Administration.objects.filter(
                backgroundinfo__in=BackgroundInfo.objects.filter(
                    source_id=kwargs.pop("source_id")
                )
            )
        qs_json = self.get_json(request, study, administrations)

        # Return CSV
        return HttpResponse(qs_json, content_type="application/json")


class AdministrationAPI(BaseAPIView):
    def post(self, request, *args, **kwargs):
        study_obj = Study.objects.get(pk=kwargs.pop("pk"))
        administrations = Administration.objects.filter(
            pk=kwargs.pop("administration_id")
        )
        qs_json = self.get_json(request, study_obj, administrations)

        # Return CSV
        return HttpResponse(qs_json, content_type="application/json")
