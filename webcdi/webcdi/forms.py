from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
