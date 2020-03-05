from django.conf.urls import url

from . import views

# URL patterns for pages related to researcher interface
urlpatterns = [
            url(r'^$', views.console, name='console'),
            url(r'^add_study/$', views.add_study, name='add_study'),
            url(r'^add_paired_study/$', views.add_paired_study, name='add_paired_study'),
            url(r'^study/(?P<study_name>[^/]+)/$', views.console, name='console'),
            url(r'^study/(?P<study_name>[^/]+)/administer_new/$', views.administer_new, name='administer_new'),
            url(r'^study/(?P<study_name>[^/]+)/import_data/$', views.import_data, name='import_data'),
            url(r'^study/(?P<study_name>[^/]+)/rename_study/$', views.rename_study, name='rename_study'),
            url(r'^(?P<username>[^/]+)/(?P<study_name>[^/]+)/new_parent/$', views.administer_new_parent, name='administer_new_parent'),
            url(r'^(?P<username>[^/]+)/(?P<study_name>[^/]+)/new_participant/$', views.administer_new_participant, name='administer_new_participant'),
            url(r'^(?P<username>[^/]+)/(?P<study_name>[^/]+)/overflow/$', views.overflow, name='overflow'),
            url(r'^edit-administration/(?P<pk>[0-9]+)/$', views.EditAdministrationView.as_view(), name='edit-administration'),
            url(r'^edit-local-lab-id/(?P<pk>[0-9]+)/$', views.EditLocalLabIdView.as_view(), name='edit-local-lab-id'),
            url(r'^edit-opt-out/(?P<pk>[0-9]+)/$', views.EditOptOutView.as_view(), name='edit-opt-out'),
            ]
