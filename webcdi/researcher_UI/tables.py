import django_tables2 as tables
from cdi_forms import views
from django_tables2.utils import A
from django.conf.urls import url
from .models import administration

class StudyAdministrationTable(tables.Table):
    select_col = tables.columns.CheckBoxColumn(accessor='id')
    link = tables.TemplateColumn('<a href="/form/fill/{{ record.url_hash }}" target="_blank">link</a>')
    class Meta:
        model = administration
        exclude = ("study",'id', 'url_hash','completedBackgroundInfo')
        sequence = ('select_col','subject_id', 'repeat_num', 'link')
        # add class="paleblue" to <table> tag
