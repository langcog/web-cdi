from django.urls import include, path

from api import views

app_name = "api"

urlpatterns = [
    path(
        "study/<int:pk>/",
        include(
            [
                path("", views.StudyAPI.as_view(), name="study_api"),
                path(
                    "source/<str:source_id>/",
                    views.SourceAPI.as_view(),
                    name="source_api",
                ),
                path(
                    "source/<str:source_id>/<str:event_id>/",
                    views.SourceAPI.as_view(),
                    name="event_api",
                ),
                path(
                    "administration/<int:administration_id>/",
                    views.AdministrationAPI.as_view(),
                    name="administration_api",
                ),
            ]
        ),
    ),
]
