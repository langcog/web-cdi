from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from webcdi.backends import login_candidates


class LoginForm(AuthenticationForm):
    """Log in with a username or an email address (#722)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username or email"

    def clean(self):
        username = self.cleaned_data.get("username")
        if username:
            users, matched_on = login_candidates(username)
            if matched_on == "email" and len(users) > 1:
                raise forms.ValidationError(
                    "More than one account uses this email address. Please log in with your username.",
                    code="ambiguous_email",
                )
        return super().clean()


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        max_length=30, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    first_name = forms.CharField(
        max_length=30, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        max_length=30, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        max_length=254,
        help_text="Required. Please provide a valid email address.",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    institution = forms.CharField(
        max_length=30, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    position = forms.CharField(
        max_length=30, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password1 = forms.CharField(
        max_length=30, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    password2 = forms.CharField(
        max_length=30, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists. "
                "If you have forgotten your username or password, use "
                "\"Forgot your password?\" on the login page; the reset email includes your username.",
                code="duplicate_email",
            )
        return email

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "institution",
            "position",
            "password1",
            "password2",
        )
