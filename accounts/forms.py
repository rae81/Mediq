from django import forms
from django.contrib.auth.models import User

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))
    
    # Extra fields for the Profile
    age = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your age'}))
    phone = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'})
        }

from .models import Doctor
from django import forms
# forms.py
from django import forms
from .models import Doctor

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'email', 'age', 'specialty', 'phone', 'profile_image']
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'})
        }

class DoctorLoginForm(forms.Form):
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all(), label="Select Doctor")
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
