from django.conf.urls import url
from django.urls import path
from . import views_endalk as views

urlpatterns = [
    url(r"^$", views.Console.as_view(), name="console"),  # progessing
    url(r"^study/(?P<study_name>[^/]+)/$", views.Console.as_view(), name="console"),
    url(r"^add_study/$", views.AddStudy.as_view(), name="add_study"),
    url(
        r"^add_paired_study/$", views.AddPairedStudy.as_view(), name="add_paired_study"
    ),
    url(
        r"^study/(?P<study_name>[^/]+)/administer_new/$",
        views.AdminNew.as_view(),
        name="administer_new",
    ),
    url(
        r"^study/(?P<study_name>[^/]+)/import_data/$",
        views.ImportData.as_view(),
        name="import_data",
    ),
    url(
        r"^study/(?P<study_name>[^/]+)/rename_study/$",
        views.RenameStudy.as_view(),
        name="rename_study",
    ),
    url(
        r"^(?P<username>[^/]+)/(?P<study_name>[^/]+)/new_parent/$",
        views.AdminNewParent.as_view(),
        name="administer_new_parent",
    ),
    url(
        r"^(?P<username>[^/]+)/(?P<study_name>[^/]+)/new_participant/$",
        views.AdministerNewParticipant.as_view(),
        name="administer_new_participant",
    ),
    url(
        r"^(?P<username>[^/]+)/(?P<study_name>[^/]+)/overflow/$",
        views.Overflow.as_view(),
        name="overflow",
    ),
    url(
        r"^edit-administration/(?P<pk>[0-9]+)/$",
        views.EditAdministrationView.as_view(),
        name="edit-administration",
    ),
    url(
        r"^edit-local-lab-id/(?P<pk>[0-9]+)/$",
        views.EditLocalLabIdView.as_view(),
        name="edit-local-lab-id",
    ),
    url(
        r"^edit-opt-out/(?P<pk>[0-9]+)/$",
        views.EditOptOutView.as_view(),
        name="edit-opt-out",
    ),
    url(r"^ajax/get_demographic_forms/$", views.AjaxDemographicForms.as_view()),
    path(
        "researcher/<int:pk>/",
        views.ResearcherAddInstruments.as_view(),
        name="researcher_add_instruments_endalk",
    ),
]