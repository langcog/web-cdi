
from django import forms

from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit

# Form for contacting Web-CDI team. Asks for basic contact information and test ID. Simple format.
class ContactForm(forms.Form):
    contact_name = forms.CharField(label=_("Your Name"), required=True, max_length=51)
    contact_email = forms.EmailField(
        label=_("Your Email Address"),
        required=True,
        max_length=201,
        validators=[EmailValidator()],
    )
    contact_id = forms.CharField(
        label=_("Your Test URL"), required=True, max_length=101
    )
    content = forms.CharField(
        label=_("What would you like to tell us?"),
        required=True,
        widget=forms.Textarea(attrs={"cols": 80, "rows": 6}),
        max_length=1001,
    )

    def __init__(self, *args, **kwargs):
        self.redirect_url = kwargs.pop("redirect_url", "")
        super().__init__(*args, **kwargs)
        self.fields["contact_id"].initial = self.redirect_url
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col-lg-9"
        self.helper.layout = Layout(
            Field("contact_name"),
            Field("contact_email"),
            Field("contact_id", css_class="form-control-plaintext"),
            Field("content"),
            Div(
                Submit("submit", _("Submit")),
                css_class="col-lg-offset-3 col-lg-9 text-center",
            ),
        )

    def send_email(self):
        cleaned_data = self.cleaned_data
        template = get_template("cdi_forms/administration_contact_email_template.txt")
        context = {
            "contact_name": cleaned_data['contact_name'],
            "contact_id": cleaned_data['contact_id'],
            "contact_email": cleaned_data['contact_email'],
            "form_content": cleaned_data['content'],
        }
        content = template.render(context)
        email = EmailMessage(
            "New contact form submission",
            content,
            settings.CONTACT_EMAIL,
            [settings.USER_ADMIN_EMAIL],
            headers={"Reply-To": cleaned_data['contact_email']},
        )
        email.send()