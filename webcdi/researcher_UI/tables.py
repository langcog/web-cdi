import django_tables2 as tables
from .models import administration

class StudyAdministrationTable(tables.Table):
    select_col = tables.columns.CheckBoxColumn(accessor='subject_id')
    class Meta:
        model = administration
        exclude = ("study",'id')
        sequence = ('select_col','subject_id', 'repeat_num', 'url_hash')
        # add class="paleblue" to <table> tag
