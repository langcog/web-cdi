import django_tables2 as tables
from cdi_forms import views
from django_tables2.utils import A
from django.conf.urls import url
from researcher_UI.models import Administration
from django.utils.html import mark_safe

# Table for organizing administration objects into a table on the researcher interface
class StudyAdministrationTable(tables.Table):
    # select_col = tables.columns.CheckBoxColumn(accessor='id') # Creates a column of checkboxes associated with each administration ID
    select_col = tables.CheckBoxColumn(
        accessor="pk", attrs={"th__input": {"onclick": "toggle(this)"}}, orderable=False
    )
    subject_id = tables.TemplateColumn(
        '<span href="/interface/edit-administration/{{ record.pk }}/">{{ record.subject_id }}</span>'
    )  # Generate Link to edit subject_id
    local_lab_id = tables.TemplateColumn(
        '<span href="/interface/edit-local-lab-id/{{ record.pk }}/">{{ record.local_lab_id }}</span>'
    )  # Generate Link to edit local_lab_id
    link = tables.TemplateColumn(
        '<a href="{{ record.get_absolute_url }}" target="_blank">link</a>',
        orderable=False,
    )  # Generates a column of administration links in each row
    analysis = tables.Column(orderable=True, order_by=["analysis", "pk"])
    opt_out = tables.TemplateColumn(
        '<span href="/interface/edit-opt-out/{{ record.pk }}/">{{ record.opt_out }}</span>'
    )

    def render_analysis(self, value):
        return (
            mark_safe('<span class="true">✔</span>')
            if value
            else mark_safe('<span class="false">✘</span>')
            if not value
            else ""
        )

    # Associates administration table with administration model
    class Meta:
        model = Administration
        exclude = (
            "study",
            "id",
            "url_hash",
            "page_number",
            "bypass",
            "include",
        )  # Excludes some fields in administration objects from table
        sequence = (
            "select_col",
            "subject_id",
            "local_lab_id",
            "repeat_num",
            "link",
        )  # Specifies column order within table
