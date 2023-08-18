from django.conf.urls import url
from django.urls import path

from researcher_UI import views

app_name = "researcher_ui"

urlpatterns = [
    path("", views.Console.as_view(), name="console"),
    path(
        "study/<int:pk>/detail/", views.StudyCreateView.as_view(), name="console_study"
    ),
    path("add_study/", views.AddStudy.as_view(), name="add_study"),
    path("add_paired_study/", views.AddPairedStudy.as_view(), name="add_paired_study"),
    path(
        "study/<int:pk>/administer_new/",
        views.AdminNew.as_view(),
        name="administer_new",
    ),
    path(
        "study/<int:pk>/import_data/",
        views.ImportData.as_view(),
        name="import_data",
    ),
    path(
        "study/<int:pk>/rename_study/", views.RenameStudy.as_view(), name="rename_study"
    ),
    path("study/<int:pk>/overflow/", views.Overflow.as_view(), name="overflow"),
    url(
        r"^(?P<username>[^/]+)/(?P<study_name>[^/]+)/new_parent/$",
        views.AddNewParent.as_view(),
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
    path(
        "ajax/get_demographic_forms/",
        views.AjaxDemographicForms.as_view(),
        name="get_demographic_forms",
    ),
    path(
        "ajax/get_charge_status/",
        views.AjaxChargeStatus.as_view(),
        name="get_charge_status",
    ),
    path(
        "researcher/<int:pk>/",
        views.ResearcherAddInstruments.as_view(),
        name="researcher_add_instruments",
    ),
    path(
        "edit-study-new/<int:pk>/",
        views.EditStudyView.as_view(),
        name="edit_study_new",
    ),
    path(
        "study/<int:pk>/pdf/",
        views.PDFAdministrationDetailView.as_view(),
        name="pdf_summary",
    ),
]
