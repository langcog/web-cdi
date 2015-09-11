from django.conf.urls import url

from . import views

urlpatterns = [
            url(r'^$', views.cdi_form, name='cdi_form'),
            ]

