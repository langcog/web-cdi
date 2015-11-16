from django.conf.urls import url

from . import views

urlpatterns = [
            url(r'^$', views.console, name='console'),
            url(r'^add_study/$', views.add_study, name='add_study'),
            url(r'^study/(?P<study_name>[^/]+)/$', views.console, name='console'),
            url(r'^study/(?P<study_name>[^/]+)/administer_new/$', views.administer_new, name='administer_new'),

            url(r'^study/(?P<study_name>[^/]+)/download_study/$', views.administer_new, name='download_study'),
            ]
