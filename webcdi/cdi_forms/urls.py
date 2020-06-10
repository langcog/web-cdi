from django.conf.urls import url, include
from django.urls import path

from . import views

# Create URLs associated with some of the functions found in views.py 'views_FUNCTION NAME'. You can look up what each function renders in views.py. URLs are referenced in webcdi/urls.py
urlpatterns = [
        url(r'demo/English_WS$', views.cdi_form, name='cdi_form'),
        url(r'background/(?P<pk>[0-9]+)/$', views.BackgroundInfoView.as_view(), name='background-info'),
        url(r'background-create/(?P<study_id>[0-9]+)/bypass/(?P<prolific_pid>[0-9a-zA-Z]+)/$', views.CreateBackgroundInfoView.as_view(), {'bypass':True}, name='create-new-background-info'),
        url(r'background-create/(?P<study_id>[0-9]+)/(?P<prolific_pid>[0-9a-zA-Z]+)/$', views.CreateBackgroundInfoView.as_view(), {'bypass':None}, name='create-new-background-info'),
        url(r'background-create/(?P<study_id>[0-9]+)/bypass/$', views.CreateBackgroundInfoView.as_view(), {'bypass':True}, name='create-new-background-info'),
        url(r'background-create/(?P<study_id>[0-9]+)/$', views.CreateBackgroundInfoView.as_view(), {'bypass':None}, name='create-new-background-info'),
        url(r'background-backpage/(?P<pk>[0-9]+)/$', views.BackpageBackgroundInfoView.as_view(), name='backpage-background-info'),
        url(r'fill/(?P<hash_id>[0-9a-f]{64})/$', views.administer_cdi_form, name='administer_cdi_form'),
        url(r'save_answer/$', views.save_answer, name='save_answer'),
        url(r'group/(?P<username>[^/]+)/(?P<study_group>[a-zA-Z0-9-_]+)/$', views.find_paired_studies, name='find_paired_studies'),
        url(r'contact/(?P<hash_id>[0-9a-f]{64})/$', views.contact, name='contact'),
        url(r'update_administration_data_item/$', views.update_administration_data_item, name="update-administration-data-item"),
        url(r'administraion-pdf-view/(?P<pk>[0-9]+)/$', views.PDFAdministrationDetailView.as_view(), name="administration-pdf-view"),
        url(r'administraion-view/(?P<pk>[0-9]+)/$', views.AdministrationDetailView.as_view(), name="administration-view"),
        path('cat/', include(('cdi_forms.cat_forms.urls', 'cat_forms'), namespace="cat_forms")),
]