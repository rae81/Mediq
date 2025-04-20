from django import forms
from django.contrib.auth.models import User
from .models import Message, Doctor

# ------------------------------
# User signup / login / profile
# ------------------------------

class SignUpForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    age = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your age'
        })
    )
    phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number'
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email address'
            }),
        }

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', "Passwords do not match")
        return cleaned


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
        }


# ------------------------------
# Patient ↔ Doctor messaging
# ------------------------------

class PatientMessageForm(forms.ModelForm):
    receiver_doctor = forms.ModelChoiceField(
        label="Doctor",
        queryset=Doctor.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    class Meta:
        model = Message
        fields = ['receiver_doctor', 'content']


class DoctorMessageForm(forms.ModelForm):
    receiver_user = forms.ModelChoiceField(
        label="Patient",
        queryset=User.objects.none(),  # set dynamically in the view
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    class Meta:
        model = Message
        fields = ['receiver_user', 'content']


# ------------------------------
# Doctor profile & login
# ------------------------------

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'email', 'age', 'specialty', 'phone', 'profile_image']
        widgets = {
            'name':       forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'age':        forms.NumberInput(attrs={'class': 'form-control'}),
            'specialty':  forms.TextInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control'}),
        }


class DoctorLoginForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        label="Select Doctor",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
