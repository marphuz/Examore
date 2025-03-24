from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.core.signals import request_finished
from django.dispatch import receiver

# Create your models here.
ANNI = (
    (1, 'Primo Anno'),
    (2, 'Secondo Anno'),
    (3, 'Terzo Anno')
)

SEMESTRI = (
    (1, '1° Semestre'),
    (2, '2° Semestre'),
    (3, 'Ciclo Annuale Unico')
)




class Facolta(models.Model):
    nome = models.CharField(max_length=200)
    durata = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nome', 'durata'], name='unique_migration_nome_anno')
        ]

        def __str__(self):
            return self.nome


class Esame(models.Model):
    nome = models.CharField(max_length=100)
    anno = models.IntegerField(choices=ANNI)
    semestre = models.IntegerField(choices=SEMESTRI)
    crediti = models.CharField(max_length=10)
    facolta = models.ForeignKey(Facolta, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'anno', 'semestre', 'facolta'], name='unique_migration_Esame'
            )
        ]

    def __str__(self):
        return self.nome


class AppelloEsame(models.Model):
    data = models.CharField(max_length=19)
    esame = models.ForeignKey(Esame, on_delete=models.CASCADE)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.esame.nome + ' ' + str(self.data)
    
    def delete(self, *args, **kwargs):
        """
        Sovrascrive il metodo delete standard per eliminare anche gli eventi Google Calendar
        associati prima di eliminare l'appello dal database.
        """
        try:
            print(f"\n===== ELIMINAZIONE APPELLO {self.id}: {self.esame.nome} =====")
            
            # Cerca tutte le sincronizzazioni associate a questo appello
            syncs = CalendarSync.objects.filter(appello=self)
            print(f"Trovate {syncs.count()} sincronizzazioni")
            
            # Elimina gli eventi Google Calendar associati
            for sync in syncs:
                try:
                    print(f"Elaborazione sincronizzazione {sync.id} per l'utente {sync.user.username}")
                    
                    # Ottieni credenziali utente
                    from allauth.socialaccount.models import SocialAccount, SocialToken
                    from google.oauth2.credentials import Credentials
                    from googleapiclient.discovery import build
                    from django.conf import settings
                    
                    social_account = SocialAccount.objects.get(user=sync.user, provider='google')
                    social_token = SocialToken.objects.get(account=social_account)
                    
                    # Crea credenziali Google
                    credentials = Credentials(
                        token=social_token.token,
                        refresh_token=social_token.token_secret,
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                        client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
                    )
                    
                    # Costruisci servizio Google Calendar
                    service = build('calendar', 'v3', credentials=credentials)
                    
                    # Elimina evento
                    print(f"Tentativo di eliminazione evento Google Calendar {sync.google_event_id}")
                    service.events().delete(
                        calendarId='primary',
                        eventId=sync.google_event_id
                    ).execute()
                    print(f"✓ Evento Google Calendar eliminato con successo")
                    
                    # Elimina record di sincronizzazione
                    sync_id = sync.id
                    sync.delete()
                    print(f"✓ Record di sincronizzazione {sync_id} eliminato")
                    
                except Exception as e:
                    import traceback
                    print(f"✗ Errore durante l'eliminazione dell'evento Google Calendar: {e}")
                    traceback.print_exc()
                    # Continua comunque con l'elaborazione degli altri eventi
            
            print("===== ELIMINAZIONE EVENTI GOOGLE CALENDAR COMPLETATA =====\n")
        except Exception as e:
            import traceback
            print(f"✗ Errore generale durante l'eliminazione degli eventi Google Calendar: {e}")
            traceback.print_exc()
            # Continua comunque con l'eliminazione dell'appello
        
        # Esegui l'eliminazione standard dell'appello
        super().delete(*args, **kwargs)

class Aula(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class DisponibilitaOraria(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    data = models.DateField()
    ora_inizio = models.CharField(max_length=6)
    ora_fine = models.CharField(max_length=6)

    class Meta:
        unique_together = ('aula', 'data', 'ora_inizio', 'ora_fine')

class CalendarSync(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    appello = models.ForeignKey(AppelloEsame, on_delete=models.CASCADE)
    google_event_id = models.CharField  (max_length=255)
    last_synced = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'appello')
        
    def __str__(self):
        return f"{self.user.username} - {self.appello.esame.nome} - {self.last_synced}"
    
@receiver(post_save, sender=AppelloEsame)
def appello_updated(sender, instance, **kwargs):
    """Segnale che viene attivato quando un appello viene salvato"""
    # Trova tutte le sincronizzazioni per questo appello
    from .models import CalendarSync
    syncs = CalendarSync.objects.filter(appello=instance)
    
    if syncs.exists():
        from .autosync import update_google_calendar_event
        for sync in syncs:
            try:
                # Aggiorna l'evento in Google Calendar
                update_google_calendar_event(sync)
            except Exception as e:
                print(f"Errore nella sincronizzazione automatica: {e}")
@receiver(request_finished)
def log_request_finished(**kwargs):
    """Log per verificare che i segnali Django funzionino"""
    print("DEBUG: Segnale request_finished attivato")

@receiver(post_delete, sender=AppelloEsame)
def appello_deleted(sender, instance, **kwargs):
    """Segnale che viene attivato quando un appello viene eliminato"""
    print(f"===== SEGNALE: Appello eliminato: {instance.id} - {instance.esame.nome} =====")
    
    try:
        appello_id=instance.id
        print(f"Appello ID: {appello_id}")
        # Cerca eventuali sincronizzazioni per questo appello
        # Nota: Dobbiamo usare l'ID direttamente perché l'istanza è già stata eliminata
        from main.models import CalendarSync  # Import esplicito per evitare problemi di circolarità
        syncs = CalendarSync.objects.filter(appello_id=instance.id)
        
        print(f"Trovate {syncs.count()} sincronizzazioni da eliminare")
        
        if syncs.exists():
            from main.autosync import delete_google_calendar_event  # Import esplicito
            for sync in syncs:
                try:
                    print(f"Tentativo di eliminare evento Google Calendar: {sync.google_event_id}")
                    # Elimina l'evento da Google Calendar
                    result = delete_google_calendar_event(sync)
                    print(f"Risultato eliminazione: {'Successo' if result else 'Fallito'}")
                    
                    # Elimina anche il record di sincronizzazione
                    sync_id = sync.id  # Salva ID per il log
                    sync.delete()
                    print(f"Record di sincronizzazione {sync_id} eliminato dal database")
                except Exception as e:
                    import traceback
                    print(f"ERRORE nell'eliminazione dell'evento/sync: {e}")
                    traceback.print_exc()
    except Exception as e:
        import traceback
        print(f"ERRORE generale nel segnale appello_deleted: {e}")
        traceback.print_exc()