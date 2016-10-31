from django.conf.urls import url

from . import views

urlpatterns = [
            url(r'demo/English_WS$', views.cdi_form, name='cdi_form'),
            url(r'fill/(?P<hash_id>[0-9a-f]{64})/$', views.administer_cdi_form, name='administer_cdi_form'),
            url(r'result/(?P<hash_id>[0-9a-f]{64})/$', views.visualize_cdi_result, name='visualize_cdi_result'),
            url(r'api/(?P<hash_id>[0-9a-f]{64})/$', views.words, name='words'),
            ]

