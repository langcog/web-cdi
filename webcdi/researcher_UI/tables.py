import django_tables2 as tables
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from researcher_UI.models import Administration


# Table for organizing administration objects into a table on the researcher interface.
#
# Ten columns: select, edit, participant ID, lab ID, admin #, link, status,
# created, expires, completed. The five completion booleans are folded into one
# Status badge (see render_status); the rarely-needed fields (last modified,
# confirmed-completion, completion-flag response, opt-out) live in the row's
# Edit dialog (table.html) or appear as a chip next to the status.
class StudyAdministrationTable(tables.Table):
    select_col = tables.CheckBoxColumn(
        accessor="pk",
        attrs={"th__input": {"onclick": "toggle(this)"}},
        orderable=False,
    )
    # Opens the per-row edit dialog defined in table.html
    edit = tables.TemplateColumn(
        '<button type="button" class="wcdi-row-edit" onclick="edit_function({{ record.pk }})" '
        'title="Edit administration {{ record.subject_id }}">'
        '<i class="fa fa-pencil" aria-hidden="true"></i><span>Edit</span></button>',
        orderable=False,
        verbose_name="",
        empty_values=(),
    )
    subject_id = tables.Column(verbose_name="Participant ID")
    local_lab_id = tables.Column(verbose_name="Lab ID", default="—")
    repeat_num = tables.Column(verbose_name="Admin #")
    link = tables.TemplateColumn(
        '<span class="wcdi-link-cell">'
        '<a href="{{ record.get_absolute_url }}" target="_blank" rel="noopener" title="Open the participant\'s link in a new tab">Open</a>'
        '<button type="button" class="wcdi-copy-link" data-link="{{ record.get_absolute_url }}" '
        'title="Copy the participant\'s link"><i class="fa fa-clone" aria-hidden="true"></i><span class="sr-only">Copy link</span></button>'
        "</span>",
        orderable=False,
        verbose_name="Link",
    )
    status = tables.Column(
        empty_values=(),
        orderable=True,
        order_by=("scored", "completed", "completedSurvey", "completedBackgroundInfo", "pk"),
    )
    created_date = tables.DateTimeColumn(verbose_name="Created")
    due_date = tables.DateTimeColumn(verbose_name="Expires")
    completed_date = tables.DateTimeColumn(verbose_name="Completed")
    # Only shown for studies that confirm age/completion (get_helper excludes it otherwise)
    analysis = tables.Column(
        verbose_name="Confirmed", orderable=True, order_by=["analysis", "pk"]
    )

    def render_status(self, record):
        now = timezone.now()
        if not record.is_active:
            kind, label, tip = "inactive", "Inactive", "Deactivated by an administrator"
        elif record.scored:
            kind, label, tip = "scored", "Scored", "Completed and scored; ready to download"
        elif record.completed:
            kind, label, tip = "done", "Completed", "Completed; scores are computed overnight"
        elif record.completedSurvey:
            kind, label, tip = "survey", "Survey pending", "CDI completed; the follow-up questions are still open"
        elif record.due_date and record.due_date < now:
            kind, label, tip = "expired", "Expired", "The link expired before the form was completed"
        elif record.completedBackgroundInfo:
            kind, label, tip = "progress", "In progress", "Background info completed; CDI in progress"
        else:
            kind, label, tip = "new", "Not started", "The link has not been used yet"
        if record.last_modified:
            tip += " · last activity " + timezone.localtime(record.last_modified).strftime("%-m/%-d/%Y %-I:%M %p")
        chip = ""
        if record.opt_out:
            chip = '<span class="wcdi-chip" title="Participant opted out of broader data sharing">opt-out</span>'
        return format_html(
            '<span class="wcdi-badge wcdi-badge-{}" title="{}">{}</span>{}',
            kind, tip, label, mark_safe(chip),
        )

    def _render_when(self, value):
        # ISO in a data attribute; table.html converts to the viewer's local time
        if not value:
            return mark_safe('<span class="wcdi-muted">—</span>')
        return format_html(
            '<time data-utc="{}">{}</time>', value.isoformat(), value.strftime("%-m/%-d/%y")
        )

    def render_created_date(self, value):
        return self._render_when(value)

    def render_due_date(self, value):
        return self._render_when(value)

    def render_completed_date(self, value):
        return self._render_when(value)

    def render_analysis(self, value):
        return (
            mark_safe('<span class="true">✔</span>')
            if value
            else mark_safe('<span class="false">✘</span>')
        )

    # Associates administration table with administration model
    class Meta:
        model = Administration
        fields = (
            "select_col",
            "edit",
            "subject_id",
            "local_lab_id",
            "repeat_num",
            "link",
            "status",
            "created_date",
            "due_date",
            "completed_date",
            "analysis",
        )
        sequence = fields
        attrs = {"class": "table wcdi-admin-table"}
        row_attrs = {"data-pk": lambda record: record.pk}
