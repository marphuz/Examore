# Validazione individuale dell'email
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


#def clean_email(self):
#       email = self.cleaned_data.get('email')

        # Controllo se l'email termina con @studenti.unimore.it o @unimore.it
       # if not email.endswith('@studenti.unimore.it') and not email.endswith('@unimore.it'):
            #raise ValidationError("L'email deve terminare con @studenti.unimore.it o @unimore.it")

        # Controllo se l'email è già stata utilizzata
        #if User.objects.filter(email=email).exists():
           # raise ValidationError("L'email è già stata utilizzata.")

       # return email

    # Validazione individuale dell'username
 #   def clean_username(self):
    #    username = self.cleaned_data.get('username')

        # Controllo se l'username è già utilizzato
    #    if User.objects.filter(username=username).exists():
    #        raise ValidationError("Questo username è già in uso.")
#
     #   return username

    # Validazione incrociata per le password
  #  def clean(self):
   #     cleaned_data = super().clean()
   #     password1 = cleaned_data.get("password1")
   #     password2 = cleaned_data.get("password2")

    #    if len(password1)<8 or len(password2)<8:
    #        raise ValidationError("La password è troppo corta, deve contenere almeno 8 caratteri")

        # Controllo che le password coincidano
    #    if password1 and password2 and password1 != password2:
     #       raise ValidationError("Le due password immesse non coincidono.")

    #    return cleaned_data