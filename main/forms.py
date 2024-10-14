from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    username_or_email = forms.CharField(label='Username o Email', max_length=255,
                                        widget=forms.TextInput(attrs={'placeholder': 'Username/Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if '@' in username_or_email:
            # if not (username_or_email.endswith('@studenti.unimore.it') or username_or_email.endswith('@unimore.it')):
            #    raise forms.ValidationError("L'email deve terminare con @studenti.unimore.it o @unimore.it")
            choice = 'email'
        else:
            choice = 'username'

        if username_or_email and password:
            if choice == 'username':
                try:
                    user = User.objects.get(username=username_or_email)
                except User.DoesNotExist:
                    raise forms.ValidationError("Utente non trovato.")
            else:
                try:
                    user = User.objects.get(email=username_or_email)
                except User.DoesNotExist:
                    raise forms.ValidationError("Utente non trovato.")

        self.user = authenticate(username=user.username, password=password)
        if self.user is None:
            raise forms.ValidationError("Password non valida.")

        return cleaned_data

    def get_user(self):
        return self.user


class RegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(label="Conferma Password",
                                widget=forms.PasswordInput(attrs={'placeholder': 'Conferma Password'}))

    # Validazione individuale dell'email
    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Controllo se l'email termina con @studenti.unimore.it o @unimore.it
        if not email.endswith('@studenti.unimore.it') and not email.endswith('@unimore.it'):
            raise ValidationError("L'email deve terminare con @studenti.unimore.it o @unimore.it")

        # Controllo se l'email è già stata utilizzata
        if User.objects.filter(email=email).exists():
            raise ValidationError("L'email è già stata utilizzata.")

        return email

    # Validazione individuale dell'username
    def clean_username(self):
        username = self.cleaned_data.get('username')

        # Controllo se l'username è già utilizzato
        if User.objects.filter(username=username).exists():
            raise ValidationError("Questo username è già in uso.")

        return username

    # Validazione incrociata per le password
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Controllo che le password coincidano
        if password1 and password2 and password1 != password2:
            raise ValidationError("Le due password immesse non coincidono.")

        return cleaned_data

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
