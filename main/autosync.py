# main/autosync.py
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .models import AppelloEsame, CalendarSync
from allauth.socialaccount.models import SocialAccount, SocialToken

def sync_appelli_changes():
    """
    Funzione da eseguire periodicamente per sincronizzare le modifiche agli appelli
    """
    # Ottieni tutte le sincronizzazioni esistenti
    syncs = CalendarSync.objects.all()
    
    for sync in syncs:
        appello = sync.appello
        
        # Controlla se l'appello è stato modificato dopo l'ultima sincronizzazione
        if appello.last_modified > sync.last_synced:
            try:
                # Aggiorna l'evento in Google Calendar
                update_google_calendar_event(sync)
                print(f"Aggiornato evento {sync.google_event_id} per appello {appello.id}")
            except Exception as e:
                print(f"Errore nell'aggiornamento dell'evento {sync.google_event_id}: {e}")

def update_google_calendar_event(sync):
    """
    Aggiorna un evento in Google Calendar
    """
    try:
        # Ottieni le credenziali dell'utente
        social_account = SocialAccount.objects.get(user=sync.user, provider='google')
        social_token = SocialToken.objects.get(account=social_account)
        
        # Crea le credenziali
        credentials = Credentials(
            token=social_token.token,
            refresh_token=social_token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
            client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
            scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.events'
            ]
        )
        
        # Inizializza il servizio Calendar
        service = build('calendar', 'v3', credentials=credentials)
        
        # Parsing della data e ora dell'appello
        appello = sync.appello
        if " - " in appello.data:
            date_str, time_str = appello.data.split(" - ")
        else:
            data_parts = appello.data.split()
            date_str = data_parts[0]
            time_str = data_parts[1] if len(data_parts) > 1 else "09:00"
        
        # Parsing della data
        day, month, year = date_str.split('/')
        
        # Parsing dell'ora
        if ':' in time_str:
            hour, minute = time_str.split(':')
        else:
            hour, minute = "09", "00"
        
        # Conversione in numeri interi
        day = int(day)
        month = int(month)
        year = int(year)
        hour = int(hour)
        minute = int(minute)
        
        # Creazione dell'oggetto datetime
        start_time = datetime(year, month, day, hour, minute)
        end_time = start_time + timedelta(hours=2)  # Assumiamo 2 ore per l'esame
        
        # Ottieni l'evento esistente
        event = service.events().get(
            calendarId='primary',
            eventId=sync.google_event_id
        ).execute()
        
        # Aggiorna i campi dell'evento
        event['summary'] = f'{appello.esame.nome}'
        event['description'] = f'Appello d\'esame per {appello.esame.nome}\nFacoltà: {appello.esame.facolta.nome}\nData e ora: {appello.data}'
        event['start'] = {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Rome',
        }
        event['end'] = {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Rome',
        }
        
        # Aggiorna l'evento
        updated_event = service.events().update(
            calendarId='primary',
            eventId=sync.google_event_id,
            body=event
        ).execute()
        
        # Aggiorna il timestamp della sincronizzazione
        sync.last_synced = timezone.now()
        sync.save()
        
        print(f"Evento {sync.google_event_id} aggiornato con successo")
        
    except Exception as e:
        print(f"Errore nell'aggiornamento dell'evento {sync.google_event_id}: {e}")
        raise
def delete_google_calendar_event(sync):
    """
    Elimina un evento da Google Calendar - versione robusta
    Ritorna True se l'eliminazione è riuscita, False altrimenti
    """
    try:
        print("\n===== INIZIO ELIMINAZIONE EVENTO GOOGLE CALENDAR =====")
        print(f"Event ID: {sync.google_event_id}")
        print(f"Appello ID: {sync.appello_id}")
        if hasattr(sync.appello, 'esame'):
            print(f"Esame: {sync.appello.esame.nome if hasattr(sync.appello.esame, 'nome') else 'N/A'}")
        print(f"Utente: {sync.user.username}")
        
        # Ottieni le credenziali dell'utente
        from allauth.socialaccount.models import SocialAccount, SocialToken
        
        try:
            social_account = SocialAccount.objects.get(user=sync.user, provider='google')
            social_token = SocialToken.objects.get(account=social_account)
            print(f"✓ Credenziali trovate per l'utente {sync.user.username}")
        except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist) as e:
            print(f"✗ Errore nel trovare le credenziali: {e}")
            return False
        
        # Crea le credenziali con gestione esplicita degli errori
        try:
            from google.oauth2.credentials import Credentials
            from django.conf import settings
            
            credentials = Credentials(
                token=social_token.token,
                refresh_token=social_token.token_secret,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                scopes=[
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.events'
                ]
            )
            print("✓ Credenziali Google create correttamente")
        except Exception as e:
            print(f"✗ Errore nella creazione delle credenziali: {e}")
            return False
        
        # Inizializza il servizio Calendar con gestione esplicita degli errori
        try:
            from googleapiclient.discovery import build
            service = build('calendar', 'v3', credentials=credentials)
            print("✓ Servizio Google Calendar inizializzato")
        except Exception as e:
            print(f"✗ Errore nell'inizializzazione del servizio Calendar: {e}")
            return False
        
        # Elimina l'evento con gestione esplicita degli errori
        try:
            print(f"Tentativo di eliminazione dell'evento {sync.google_event_id}...")
            service.events().delete(
                calendarId='primary',
                eventId=sync.google_event_id
            ).execute()
            print(f"✓ Evento {sync.google_event_id} eliminato con successo!")
            print("===== ELIMINAZIONE COMPLETATA CON SUCCESSO =====\n")
            return True
        except Exception as e:
            print(f"✗ Errore nell'eliminazione dell'evento: {e}")
            # Se l'errore è "Not Found", l'evento potrebbe essere già stato eliminato
            if "404" in str(e):
                print("L'evento potrebbe essere già stato eliminato.")
                return True  # Considera come successo
            return False
        
    except Exception as e:
        import traceback
        print(f"\n===== ERRORE GENERALE NELL'ELIMINAZIONE =====")
        print(f"Errore: {e}")
        traceback.print_exc()
        print("===== FINE ERRORE =====\n")
        return False
