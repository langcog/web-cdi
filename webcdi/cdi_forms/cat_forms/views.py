import json
import logging
import os.path

from django.conf import settings
from django.db.models import Min
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone, translation
from django.views import View
from django.views.generic import UpdateView

from cdi_forms.models import BackgroundInfo, requests_log
from cdi_forms.views import (PROJECT_ROOT, BackgroundInfoView,
                             BackpageBackgroundInfoView,
                             CreateBackgroundInfoView, language_map)
from researcher_UI.models import Administration

from .cdi_cat_api import cdi_cat_api
from .forms import CatItemForm
from .models import CatResponse
from .utils import string_bool_coerce

# Get an instance of a logger
logger = logging.getLogger("debug")

CAT_LANG_DICT = settings.CAT_LANG_DICT

_CAT_BANKS = {}


def _cat_bank(code):
    """Load (and cache) the static item bank used by the browser engine."""
    if code not in _CAT_BANKS:
        path = os.path.join(
            settings.BASE_DIR, "cdi_forms", "static", "cdi_forms", "cat", f"{code}.json"
        )
        with open(path, encoding="utf8") as f:
            _CAT_BANKS[code] = json.load(f)
    return _CAT_BANKS[code]


# Create your views here.


class CATBackgroundInfoView(BackgroundInfoView):
    pass


class CATCreateBackgroundInfoView(CreateBackgroundInfoView):
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CATBackpageBackgroundInfoView(BackpageBackgroundInfoView):
    pass


class CatAnswerView(View):
    """JSON endpoint for the in-browser CAT engine: persists one answer per
    POST (mirroring what the remote-engine flow stores per page load) and
    applies the completion rules when the engine reports the stopping rule."""

    def post(self, request, hash_id):
        administration = get_object_or_404(Administration, url_hash=hash_id)
        if administration.completed or administration.due_date < timezone.now():
            return JsonResponse({"error": "closed"}, status=409)

        try:
            data = json.loads(request.body)
            index = int(data["index"])
            definition = str(data["definition"])
            response_value = bool(data["response"])
            est_theta = float(data["est_theta"])
            done = bool(data.get("done"))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return JsonResponse({"error": "bad payload"}, status=400)

        cat_response, _ = CatResponse.objects.get_or_create(
            administration=administration
        )
        administered_items = cat_response.administered_items or []
        administered_words = cat_response.administered_words or []
        administered_responses = cat_response.administered_responses or []

        administered_items.append(index)
        administered_words.append(definition)
        administered_responses.append(response_value)

        cat_response.administered_items = administered_items
        cat_response.administered_words = administered_words
        cat_response.administered_responses = administered_responses
        cat_response.est_theta = est_theta
        cat_response.save()

        requests_log.objects.create(url_hash=hash_id, request_type="POST")

        completed = False
        if done or len(administered_items) >= 50:
            try:
                filename = os.path.realpath(
                    PROJECT_ROOT + administration.study.demographic.path
                )
            except Exception:
                filename = "None"
            if os.path.isfile(filename):
                administration.completedSurvey = True
            else:
                administration.completed = True
            administration.scored = True
            administration.save()
            completed = True

        return JsonResponse(
            {"ok": True, "completed": completed, "count": len(administered_items)}
        )


class AdministerAdministraionView(UpdateView):
    model = Administration
    refresh = False
    hash_id = None
    form_class = CatItemForm
    template_name = "cdi_forms/cat_forms/cat_form.html"
    word = None
    instrument_items = None
    max_words = 50
    min_words = 20
    min_error = 0.15
    est_theta = None

    def get_yes_responses(self):
        yes_list = []
        yes_list = [
            x
            for x, y in zip(
                self.object.catresponse.administered_items,
                self.object.catresponse.administered_responses,
            )
            if y
        ]
        return yes_list

    def get_hardest_easiest(self):
        if not self.object.catresponse.administered_items:
            return None, None
        yes_indices = [
            x
            for x, y in zip(
                self.object.catresponse.administered_items,
                self.object.catresponse.administered_responses,
            )
            if y
        ]
        if not yes_indices:
            return None, None
        if settings.CAT_ENGINE == "browser":
            # Same rule as the R API: easiest = max easiness intercept
            # (d = -a*b in classic parameterization), hardest = min.
            bank = {
                it["index"]: it
                for it in _cat_bank(CAT_LANG_DICT[self.language])["items"]
            }
            yes_items = [bank[i] for i in yes_indices if i in bank]
            if not yes_items:
                return None, None
            easiness = lambda it: -it["a"] * it["b"]
            easiest = max(yes_items, key=easiness)["definition"]
            hardest = min(yes_items, key=easiness)["definition"]
            return hardest, easiest
        yes_list = self.get_yes_responses()
        hardest = cdi_cat_api(
            f"hardestWord?items={yes_list}&language={CAT_LANG_DICT[self.language]}"
        )["definition"]
        easiest = cdi_cat_api(
            f"easiestWord?items={yes_list}&language={CAT_LANG_DICT[self.language]}"
        )["definition"]
        return hardest, easiest

    def get_object(self, queryset=None):
        try:
            self.hash_id = self.kwargs["hash_id"]
            obj = Administration.objects.get(url_hash=self.hash_id)
        except Exception as e:
            raise Http404("Administration not found")
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "btn-back" in request.POST:
            return redirect(
                "cat_forms:background-info", pk=self.object.backgroundinfo.id
            )
        if "word_id" not in request.POST:
            # browser-engine pages answer via CatAnswerView; a bare POST here
            # (e.g. an accidental form submit) should not 500
            return redirect("cat_forms:administer_cat_form", hash_id=self.hash_id)

        administered_responses = self.object.catresponse.administered_responses or []
        administered_words = self.object.catresponse.administered_words or []
        administered_items = self.object.catresponse.administered_items or []

        self.word = {
            "index": self.request.POST["word_id"],
            "definition": self.request.POST["label"],
        }

        administered_words.append(self.word["definition"])
        if "yes" in self.request.POST:
            administered_responses.append(True)
        else:
            administered_responses.append(False)

        administered_items.append(self.word["index"])

        self.object.catresponse.administered_responses = administered_responses
        self.object.catresponse.administered_items = administered_items
        self.object.catresponse.administered_words = administered_words
        self.object.catresponse.save()

        if len(administered_items) > 49:
            try:
                filename = os.path.realpath(
                    PROJECT_ROOT + self.object.study.demographic.path
                )
            except Exception:
                filename = "None"
            if os.path.isfile(filename):
                self.object.completedSurvey = True
            else:
                self.object.completed = True
            self.object.scored = True
            self.object.save()

        self.request.METHOD = "GET"
        return redirect("cat_forms:administer_cat_form", hash_id=self.hash_id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["language_code"] = language_map(self.object.study.instrument.language)

        if self.word:
            ctx["word"] = self.word
            ctx["form"] = CatItemForm(
                context={"label": self.word["definition"]},
                initial={
                    "word_id": self.word["index"],
                    "label": self.word["definition"],
                },
            )
            try:
                if "*" in self.word["definition"]:
                    ctx["footnote"] = True
            except AttributeError:
                pass

        ctx["max_words"] = self.max_words
        try:
            if self.object.catresponse.administered_words:
                ctx["words_shown"] = len(self.object.catresponse.administered_words) + 1
            else:
                ctx["words_shown"] = 1
            ctx["est_theta"] = self.est_theta
            ctx["due_date"] = self.object.due_date.strftime("%b %d, %Y, %I:%M %p")
            ctx["hardest"], ctx["easiest"] = self.get_hardest_easiest()
        except:
            # we get here if the form is expired without being opened
            ctx["words_shown"] = 0
            ctx["est_theta"] = self.est_theta
            ctx["due_date"] = self.object.due_date.strftime("%b %d, %Y, %I:%M %p")
            ctx["hardest"], ctx["easiest"] = None, None
        return ctx

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        user_language = language_map(self.object.study.instrument.language)
        self.language = user_language
        translation.activate(user_language)
        if not self.object.completed and self.object.due_date < timezone.now():
            response = render(
                request, "cdi_forms/expired.html", {}
            )  # Render contact form template
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
            return response
        requests_log.objects.create(url_hash=self.hash_id, request_type="GET")
        if self.object.completed or self.object.due_date < timezone.now():
            response = render(
                request,
                "cdi_forms/cat_forms/cat_completed.html",
                context=self.get_context_data(),
            )
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
            return response
        background_instance, created = BackgroundInfo.objects.get_or_create(
            administration=self.object
        )
        if self.object.completedSurvey:
            return redirect("backpage-background-info", pk=background_instance.pk)
        elif not self.object.completedBackgroundInfo:
            return redirect("background-info", pk=background_instance.pk)

        cat_response, created = CatResponse.objects.get_or_create(
            administration=self.object
        )
        if created or not cat_response.est_theta:
            cat_response.est_theta = self.est_theta
            cat_response.save()

        administered_responses = self.object.catresponse.administered_responses or []
        administered_items = self.object.catresponse.administered_items or []
        administered_words = self.object.catresponse.administered_words or []
        self.est_theta = self.object.catresponse.est_theta

        if settings.CAT_ENGINE == "browser" and self.language in CAT_LANG_DICT:
            # The validated jsCat engine runs client-side; answers come back
            # through CatAnswerView. No calls to the R API.
            ctx = {
                "title": "Web-CDI",
                "hash_id": self.hash_id,
                "object": self.object,
                "language_code": user_language,
                "cat_bank_code": CAT_LANG_DICT[self.language],
                "cat_age": self.object.backgroundinfo.age or 30,
                "cat_state_json": json.dumps(
                    {
                        "items": administered_items,
                        "responses": [bool(r) for r in administered_responses],
                    }
                ),
                "cat_max_words": self.max_words,
                "words_shown": len(administered_words) + 1,
                "due_date": self.object.due_date.strftime("%b %d, %Y, %I:%M %p"),
                "completed": False,
            }
            response = render(
                request, "cdi_forms/cat_forms/cat_form_browser.html", ctx
            )
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
            return response

        if len(administered_words) < 1:  # first word might be specified by age
            self.word = cdi_cat_api(
                f"startItem?age_mos={self.object.backgroundinfo.age}&language={CAT_LANG_DICT[self.language]}"
            )
            if self.word["definition"] is None:
                self.word = cdi_cat_api(
                    f"startItem?age_mos=30&language={CAT_LANG_DICT[self.language]}"
                )
        else:
            self.word = cdi_cat_api(
                f"nextItem?responses={list(map(int,administered_responses))}&items={administered_items}&language={CAT_LANG_DICT[self.language]}"
            )
            if self.word["stop"] == True:
                try:
                    filename = os.path.realpath(
                        PROJECT_ROOT + self.object.study.demographic.path
                    )
                except Exception:
                    filename = "None"
                if os.path.isfile(filename):
                    self.object.completedSurvey = True
                else:
                    self.object.completed = True
                self.object.scored = True
                self.object.catresponse.est_theta = self.word["curTheta"]
                self.object.save()
                self.object.catresponse.save()
                return redirect("cat_forms:administer_cat_form", hash_id=self.hash_id)
            else:
                self.object.catresponse.est_theta = self.word["curTheta"]
                self.object.save()
                self.object.catresponse.save()
        return super().get(request, *args, **kwargs)
