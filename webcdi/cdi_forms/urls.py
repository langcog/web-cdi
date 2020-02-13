from django.conf.urls import url

from . import views

# Create URLs associated with some of the functions found in views.py 'views_FUNCTION NAME'. You can look up what each function renders in views.py. URLs are referenced in webcdi/urls.py
urlpatterns = [
            url(r'demo/English_WS$', views.cdi_form, name='cdi_form'),
            url(r'background/(?P<pk>[0-9]+)/$', views.BackgroundInfoView.as_view(), name='background-info'),
            url(r'background-create/(?P<study_id>[0-9]+)/bypass/$', views.CreateBackgroundInfoView.as_view(), {'bypass':True}, name='create-new-background-info'),
            url(r'background-create/(?P<study_id>[0-9]+)/$', views.CreateBackgroundInfoView.as_view(), {'bypass':None}, name='create-new-background-info'),
            url(r'background-backpage/(?P<pk>[0-9]+)/$', views.BackpageBackgroundInfoView.as_view(), name='backpage-background-info'),
            url(r'fill/(?P<hash_id>[0-9a-f]{64})/$', views.administer_cdi_form, name='administer_cdi_form'),
            url(r'save_answer/$', views.save_answer, name='save_answer'),
            url(r'group/(?P<username>[^/]+)/(?P<study_group>[a-zA-Z0-9-_]+)/$', views.find_paired_studies, name='find_paired_studies'),
            url(r'contact/(?P<hash_id>[0-9a-f]{64})/$', views.contact, name='contact'),
            url(r'update_administration_data_item/$', views.update_administration_data_item, name="update-administration-data-item")
            ]

