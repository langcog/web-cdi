from django.urls import path

from . import views

# Create URLs associated with some of the functions found in views.py 'views_FUNCTION NAME'. You can look up what each function renders in views.py. URLs are referenced in webcdi/urls.py
urlpatterns = [
    path(
        "background/<int:pk>/",
        views.CATBackgroundInfoView.as_view(),
        name="background-info",
    ),
    path(
        "background-create/<int:study_id>/bypass/<slug:source_id>/",
        views.CATCreateBackgroundInfoView.as_view(),
        {"bypass": True},
        name="create-new-background-info",
    ),
    path(
        "background-create/<int:study_id>/<slug:source_id>/",
        views.CATCreateBackgroundInfoView.as_view(),
        {"bypass": None},
        name="create-new-background-info",
    ),
    path(
        "background-backpage/<int:pk>/",
        views.CATBackpageBackgroundInfoView.as_view(),
        name="backpage-background-info",
    ),
    path(
        "fill/<hash_id>/",
        views.AdministerAdministraionView.as_view(),
        name="administer_cat_form",
    ),
]
