
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Account


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['phone_number']


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=255)
    first_name = forms.CharField(max_length=35, label='Forename')
    last_name = forms.CharField(max_length=35, label='Surname')

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2'
        ]


class UserUpdateForm(forms.ModelForm):

    email = forms.EmailField(max_length=255)
    first_name = forms.CharField(min_length=4, max_length=35, label='Forename')
    last_name = forms.CharField(min_length=4, max_length=35, label='Surname')
    
    confirm_password = forms.CharField(widget=forms.PasswordInput, help_text='Enter your password to confirm changes')

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'confirm_password'
        ]
