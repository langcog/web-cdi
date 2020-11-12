"""webcdi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.views.generic import TemplateView
from supplementtut.views import *
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="researcher_UI/home.html")),
    url(r'^favicon\.ico', RedirectView.as_view(url='/static/images/favicon.ico', permanent=True)),
    url(r'^robots\.txt', RedirectView.as_view(url='/static/robots.txt', permanent=True)),
    url(r'^wcadmin/', admin.site.urls),
    url(r'^form/', include('cdi_forms.urls')),
    #path('cat/', include(('cdi_forms.cat_forms.urls', 'cat_forms'), namespace="cat_forms")),
    url(r'^accounts/login/$', auth_views.LoginView.as_view(), {'template_name': 'registration/login.html'}),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view(), {'next_page': 'interface/'}),
    url(r'^accounts/profile/$', RedirectView.as_view(url='/interface/', permanent=False), name='interface'),
    url(r'interface/', include('researcher_UI.urls')),
    url(r'^registration/', include('registration.urls')),
    url(r'^lockout/$', TemplateView.as_view(template_name="registration/lockout.html")),
    url(r'^health/?', include('health_check.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)