from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=250, help_text='eg. youremail@gmail.com')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password1', 'password2', 'email')


class EditUserProfileForm(UserChangeForm):
    password = None
    username = forms.CharField(disabled=True)
    date_joined = forms.DateTimeField(disabled=True)
    last_login = forms.DateTimeField(disabled=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 
                  'date_joined', 'last_login']


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email')

    class Meta:
        model = User
        fields = ['username', 'password']
