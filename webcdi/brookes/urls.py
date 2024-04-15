from django.urls import path

from brookes import views

app_name = "brookes"

urlpatterns = [
    path(
        "codes/<int:instrument_family>/",
        views.UpdateBrookesCode.as_view(),
        name="enter_codes",
    ),
]
