from django.conf.urls import url
from django.urls import path, include

from researcher_UI import views

app_name = "researcher_ui"

urlpatterns = [
    path("", views.Console.as_view(), name="console"),
    path(
        "study/",
        include(
            [
                path("<int:pk>/detail/", views.StudyCreateView.as_view(), name="console_study"), 
                path("add/", views.AddStudy.as_view(), name="add_study"),
                path("add_paired/", views.AddPairedStudy.as_view(), name="add_paired_study"),
                path("<int:pk>/administer_new/", views.AdminNew.as_view(), name="administer_new"),
                path("<int:pk>/import_data/", views.ImportData.as_view(), name="import_data",),
                path("<int:pk>/update/", views.UpdateStudyView.as_view(), name="rename_study"),
                path("<int:pk>/overflow/", views.Overflow.as_view(), name="overflow"),
            ]
        )
    ),

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
        views.AddInstruments.as_view(),
        name="researcher_add_instruments",
    ),
    path(
        "edit-study-new/<int:pk>/",
        views.EditAdministrationView.as_view(),
        name="edit_study_new",
    ),
    path(
        "study/<int:pk>/pdf/",
        views.PDFAdministrationDetailView.as_view(),
        name="pdf_summary",
    ),
    path(
        "study/<int:pk>/pdf/<str:adjusted>/",
        views.PDFAdministrationDetailView.as_view(),
        name="pdf_summary_adjusted",
    ),
]
