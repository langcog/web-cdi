from django.urls import path, include

from api import views

app_name = "api"

urlpatterns = [
    path(
        "study/<int:pk>/",
        include(
            [
                path('', views.StudyAPI.as_view()),
                path('source/<str:source_id>/', views.SourceAPI.as_view()), 
                path('source/<str:source_id>/<str:event_id>/', views.SourceAPI.as_view()), 
                path('administration/<int:administration_id>/', views.AdministrationAPI.as_view()),
            ]
        )
    ),
]
