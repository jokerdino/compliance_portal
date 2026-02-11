from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        ),
        label="",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
        label="",
    )

    class Meta:
        model = get_user_model()
        fields = ["username", "password"]


class UserCreateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = get_user_model()
        fields = ["username", "groups", "department", "email_address"]


class UserUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = get_user_model()
        fields = [
            "department",
            "groups",
            "reset_password",
            "email_address",
        ]


# class UploadExcelForm(forms.Form):
#     file = forms.FileField()
