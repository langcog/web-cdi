from django.urls import path, include

from api import views

app_name = "api"

urlpatterns = [
    path('study/<int:pk>/', views.StudyAPI.as_view()),
    path('study/<int:pk>/source/<str:source_id>/', views.SourceAPI.as_view()), 
    path('study/<int:pk>/administration/<int:administration_id>/', views.AdministrationAPI.as_view()),
    
]
