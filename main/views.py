from allauth.socialaccount.models import SocialAccount, SocialToken
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from main.autosync import update_google_calendar_event
from .forms import LoginForm, RegisterForm
from django.contrib.auth import login, authenticate
from scraping_creatingmodels import create, scraping
from .models import CalendarSync, Facolta, Esame, AppelloEsame, Aula, DisponibilitaOraria
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from googleapiclient.discovery import build
from django.conf import settings
from google.oauth2.credentials import Credentials
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
import requests
from urllib.parse import urlencode
from django.utils import timezone
from django.contrib.auth.models import User
import re

# COSTANTI:
DAY_SELECTED = None
MONTH_SELECTED = None
YEAR_SELECTED = None
CRIT = None

# FILTER FUNCTIONS:

def filterAppelli(anno_esame, periodo_esame, data_stringa, facolta_id=None):
    if anno_esame == "" or anno_esame is None:
        anno_esame = 0
    if periodo_esame == "" or periodo_esame is None:
        periodo_esame = 0
    if anno_esame != "" and periodo_esame == "":
        anno_esame = int(anno_esame)
        periodo_esame = 0
    elif anno_esame == "" and periodo_esame != "":
        anno_esame = 0
        periodo_esame = int(periodo_esame)

    appelli_attuali = None

    if facolta_id is None:
        if anno_esame == 0 and periodo_esame == 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa)
        elif anno_esame != 0 and periodo_esame == 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__anno=anno_esame)
        elif anno_esame == 0 and periodo_esame != 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__semestre=periodo_esame)
        else:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__anno=anno_esame,
                                                          esame__semestre=periodo_esame)
    else:
        f = Facolta.objects.get(id=facolta_id)
        if anno_esame == 0 and periodo_esame == 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f)
        elif anno_esame != 0 and periodo_esame == 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f,
                                                          esame__anno=anno_esame)
        elif anno_esame == 0 and periodo_esame != 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f,
                                                          esame__semestre=periodo_esame)
        else:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f,
                                                          esame__anno=anno_esame,
                                                          esame__semestre=periodo_esame)

    return appelli_attuali


def checkDisp(disp_input):
    day, month, year = None, None, None
    rgx = r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$"
    if disp_input == "" or disp_input is None or not re.match(rgx, disp_input):
        return day, month, year

    day = disp_input[:2]
    month = disp_input[3:5]
    year = disp_input[6:]

    return day, month, year


# VIEWS :
def home(request):
    return render(request, "main/base.html", {})


def esami(request):
    facolta = Facolta.objects.all()
    return render(request, "main/esami.html", {"facolta": facolta})


def calendar(request):
    global DAY_SELECTED, MONTH_SELECTED, YEAR_SELECTED
    facolta = Facolta.objects.all()
    aule = Aula.objects.all()
    aule_select_filter = Aula.objects.all()
    aule_disponibilita = {}
    anno_esame = request.POST.get('anno_esame')
    periodo_esame = request.POST.get('periodo_esame')
    aula_visible = request.POST.get('aula_visible')
    disp_input = request.POST.get('disp-input')
    facolta_id = request.GET.get('facolta_id')
    var_disp = False
    facolta_appelli = None
    if facolta_id is not None:
        facolta_appelli = facolta_id
    else:
        facolta_appelli = request.POST.get('facolta_appelli')

    day_false = request.POST.get('selectedDay')
    month_false = request.POST.get('selectedMonth')
    year_false = request.POST.get('selectedYear')

    if day_false is None and month_false is None and year_false is None and DAY_SELECTED is None and MONTH_SELECTED is None and YEAR_SELECTED is None:
        today = datetime.today()
        day = today.strftime("%d")
        month = today.strftime("%m")
        year = today.strftime("%Y")
    else:
        if DAY_SELECTED is None and MONTH_SELECTED is None and YEAR_SELECTED is None:
            day = day_false
            month = month_false
            year = year_false
            DAY_SELECTED = day_false
            MONTH_SELECTED = month_false
            YEAR_SELECTED = year_false
        else:
            day = DAY_SELECTED
            month = MONTH_SELECTED
            year = YEAR_SELECTED
            if disp_input:
                day, month, year = checkDisp(disp_input)

    data_titolo_aule = None

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        day_false = request.POST.get('selectedDay')
        month_false = request.POST.get('selectedMonth')
        year_false = request.POST.get('selectedYear')
        if day_false is not None and month_false is not None and year_false is not None:
            day = day_false
            month = month_false
            year = year_false
            DAY_SELECTED = day_false
            MONTH_SELECTED = month_false
            YEAR_SELECTED = year_false

        data_attuale = date(int(year), int(month), int(day))
        data_stringa = data_attuale.strftime("%d/%m/%Y")

        if facolta_appelli is not None:
            facolta_id = facolta_appelli

        appelli_attuali = filterAppelli(anno_esame, periodo_esame, data_stringa, facolta_id)

        if aula_visible:
            aule = Aula.objects.filter(nome=aula_visible)


        for aula in aule:
            disp = DisponibilitaOraria.objects.filter(aula=aula, data=data_attuale)
            if not disp:
                var_disp = True
                #create.createAuleDisponibilita(day, month, year)
                #disp = DisponibilitaOraria.objects.filter(aula=aula, data=data_attuale)

            aule_disponibilita[aula.nome] = [{"ora_inizio": d.ora_inizio, "ora_fine": d.ora_fine} for d in
                                             disp]

        # Risposta JSON per AJAX
        return JsonResponse({
            "appelli": [
                {
                    "id": appello.id,
                    "esame": appello.esame.nome,
                    "data": appello.data
                } for appello in appelli_attuali
            ],
            "aule_disponibilita": aule_disponibilita,
            "data_attuale": data_stringa,
            "anno_esame": anno_esame,
            "periodo_esame": periodo_esame,
            "var_disp": var_disp,

        })
    else:
        data_attuale = date(int(year), int(month), int(day))
        data_stringa = data_attuale.strftime("%d/%m/%Y")
        appelli_attuali = filterAppelli(anno_esame, periodo_esame, data_stringa, facolta_id)
        for a in aule:
            disp = DisponibilitaOraria.objects.filter(aula=a, data=data_attuale)

            # if not disp:
            #    try:
            #       create.createAuleDisponibilita(day, month, year)
            #      disp = DisponibilitaOraria.objects.filter(aula=a, data=data_attuale)

            # except:
            #    pass
            aule_disponibilita[a] = disp

    context = {
        "aule": aule,
        "data_attuale": data_stringa,
        "aule_disponibilita": aule_disponibilita,
        "appelli": appelli_attuali,
        "anno_esame": anno_esame,
        "periodo_esame": periodo_esame,
        "aule_select_filter": aule_select_filter,
        "day_selected": DAY_SELECTED,
        "month_selected": MONTH_SELECTED,
        "year_selected": YEAR_SELECTED,
        "facolta": facolta,
        "var_disp": var_disp,
        "facolta_id": facolta_id,  # Add this to help with select options
        "aula_visible": aula_visible,
    }
    return render(request, "main/calendar.html", context)


def scrapingOnDemand(request):
    data_attuale = request.GET.get('data_attuale')
    day, month, year = None, None, None

    if request.method == 'POST':
        data_attuale = request.POST.get('data_attuale')
        if data_attuale is not None:
            day = data_attuale[:2]
            month = data_attuale[3:5]
            year = data_attuale[6:]

        if 'scr' in request.POST:
            if day is not None and month is not None and year is not None:
                try:
                    create.createAuleDisponibilita(day, month, year)
                except:
                    pass

            return redirect('calendar')
        else:

            return redirect('calendar')

    context = {
        "data_attuale": data_attuale,
    }

    return render(request, "main/scraping.html", context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect('/')
    else:
        form = LoginForm()

    return render(request, "main/registration/login.html", {'form': form})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")

    else:
        form = RegisterForm()
    return render(request, "main/registration/register.html", {"form": form})

@login_required
def start_google_auth(request):
    """Inizia il processo di autenticazione con Google"""
    try:
        # Ottieni il client_id dalle impostazioni
        client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
        
        # Costruisci l'URL di autorizzazione
        
        auth_url = 'https://accounts.google.com/o/oauth2/auth'
        params = {
            'client_id': client_id,
            'redirect_uri': 'http://localhost:8000/handle_google_token/',
            'response_type': 'code',
            'scope': ' '.join([
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.events'
            ]),
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        # Reindirizza all'URL di autorizzazione
        return redirect(f"{auth_url}?{urlencode(params)}")
    except Exception as e:
        print(f"Errore nell'avvio dell'autenticazione: {str(e)}")
        return HttpResponse(f"Errore: {str(e)}")

@login_required
def handle_google_token(request):
    """Gestisce il codice di autorizzazione ricevuto da Google"""
    code = request.GET.get('code')
    if not code:
        return HttpResponse("Nessun codice di autorizzazione ricevuto")
    
    try:
        # Ottieni le credenziali
        client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
        client_secret = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret']
        
        # Scambia il codice con un token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:8000/handle_google_token/',
            'grant_type': 'authorization_code'
        }
        
        # Richiedi il token
        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            return HttpResponse(f"Errore nella richiesta del token: {token_response.text}")
        
        token_data = token_response.json()
        
        # Estrai i token
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 3600)
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Ottieni info utente
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        
        # Salva l'account social e il token
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
        except SocialAccount.DoesNotExist:
            social_account = SocialAccount.objects.create(
                user=request.user,
                provider='google',
                uid=user_info.get('id'),
                extra_data=user_info
            )
        
        # Salva il token
        social_token, created = SocialToken.objects.get_or_create(account=social_account)
        social_token.token = access_token
        social_token.token_secret = refresh_token
        social_token.expires_at = expires_at
        social_token.save()
        
        # Sincronizza con Google Calendar
        return sync_calendar_and_redirect(request)
    except Exception as e:
        print(f"Errore nella gestione del token: {str(e)}")
        return HttpResponse(f"Errore: {str(e)}")

@login_required
def sync_calendar_and_redirect(request):
    """Sincronizzazione con Google Calendar che gestisce correttamente i duplicati"""
    try:
        print("===== INIZIO SINCRONIZZAZIONE CON GOOGLE CALENDAR =====")
        
        # Recupera filtri attivi
        anno_esame = request.POST.get('anno_esame', request.GET.get('anno_esame', ''))
        periodo_esame = request.POST.get('periodo_esame', request.GET.get('periodo_esame', ''))
        facolta_id = request.POST.get('facolta_id', request.GET.get('facolta_id', ''))
        
        print(f"Filtri applicati: Anno={anno_esame}, Periodo={periodo_esame}, Facoltà={facolta_id}")
        
        # Ottieni le credenziali dell'utente
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            social_token = SocialToken.objects.get(account=social_account)
            
            credentials = Credentials(
                token=social_token.token,
                refresh_token=social_token.token_secret,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
            )
            
            # Inizializza il servizio Calendar
            service = build('calendar', 'v3', credentials=credentials)
            print("Servizio Google Calendar inizializzato con successo")
            
        except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist) as e:
            print(f"Errore di autenticazione: {e}")
            return redirect('start_google_auth')
        
        # -------------------------
        # FASE 1: PULIZIA PRELIMINARE DELLA TABELLA CALENDARSYNC
        # -------------------------
        
        # Rimuovi record inconsistenti (dove non esiste l'appello o l'utente)
        inconsistent_syncs = 0
        for sync in CalendarSync.objects.filter(user=request.user):
            try:
                # Verifica se l'appello esiste ancora
                AppelloEsame.objects.get(id=sync.appello.id)
            except AppelloEsame.DoesNotExist:
                print(f"Rimosso record inconsistente: appello {sync.appello_id} non esiste più")
                sync.delete()
                inconsistent_syncs += 1
        
        print(f"Rimossi {inconsistent_syncs} record inconsistenti dalla tabella CalendarSync")
        
        # -------------------------
        # FASE 2: VERIFICA DUPLICATI IN GOOGLE CALENDAR
        # -------------------------
        
        # Ottieni tutti gli eventi nell'intervallo di tempo ragionevole
        now = datetime.now()
        time_min = (now - timedelta(days=30)).isoformat() + 'Z'  # Un mese fa
        time_max = (now + timedelta(days=365)).isoformat() + 'Z'  # Un anno avanti
        
        print(f"Ricerca eventi esistenti in Google Calendar tra {time_min} e {time_max}")
        
        try:
            # Cerca tutti gli eventi esistenti per questo utente
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=500,  # Numero ragionevole di risultati
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            calendar_events = events_result.get('items', [])
            print(f"Trovati {len(calendar_events)} eventi esistenti in Google Calendar")
            
            # Mappa degli eventi per titolo (per un controllo veloce dei duplicati)
            event_map = {}
            for event in calendar_events:
                title = event.get('summary', '')
                if title not in event_map:
                    event_map[title] = []
                event_map[title].append(event)
            
            # Rimuovi duplicati per ogni titolo
            duplicates_removed = 0
            for title, events in event_map.items():
                if len(events) > 1:
                    print(f"Trovati {len(events)} duplicati per l'evento '{title}'")
                    
                    # Controlla se abbiamo una sincronizzazione nel DB per qualsiasi di questi eventi
                    event_ids = [event['id'] for event in events]
                    syncs = CalendarSync.objects.filter(user=request.user, google_event_id__in=event_ids)
                    synced_ids = [sync.google_event_id for sync in syncs]
                    
                    # Se esistono record nel DB, conserva questi e rimuovi gli altri
                    if synced_ids:
                        for event in events:
                            if event['id'] not in synced_ids:
                                print(f"Elimino evento duplicato non tracciato: {event['id']}")
                                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                                duplicates_removed += 1
                    else:
                        # Conserva solo il primo evento, rimuovi gli altri
                        keep_event = events[0]
                        for event in events[1:]:
                            print(f"Elimino evento duplicato: {event['id']}")
                            service.events().delete(calendarId='primary', eventId=event['id']).execute()
                            duplicates_removed += 1
            
            print(f"Rimossi {duplicates_removed} eventi duplicati da Google Calendar")
            
        except Exception as e:
            print(f"Errore durante la pulizia dei duplicati: {e}")
        
        # -------------------------
        # FASE 3: PULIZIA EVENTI PASSATI
        # -------------------------
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        past_events_removed = 0
        
        syncs = list(CalendarSync.objects.filter(user=request.user))
        print(f"Verifico {len(syncs)} sincronizzazioni esistenti per eventi passati")
        
        for sync in syncs:
            try:
                # Estrai la data dell'appello
                date_str = sync.appello.data.split(" - ")[0] if " - " in sync.appello.data else sync.appello.data.split()[0]
                day, month, year = map(int, date_str.split('/'))
                appello_date = datetime(year, month, day).date()
                
                # Se l'appello è già passato, rimuovi l'evento
                if appello_date < today.date():
                    try:
                        print(f"Rimozione evento passato: {sync.appello.esame.nome} del {date_str}")
                        service.events().delete(calendarId='primary', eventId=sync.google_event_id).execute()
                        sync.delete()
                        past_events_removed += 1
                    except Exception as e:
                        # Se l'evento non esiste più su Google Calendar, rimuovi solo il record
                        if "404" in str(e):
                            print(f"Evento non trovato su Google Calendar, rimuovo solo il record: {sync.google_event_id}")
                            sync.delete()
                            past_events_removed += 1
                        else:
                            print(f"Errore nella rimozione dell'evento passato: {e}")
            except Exception as e:
                print(f"Errore nell'elaborazione della sincronizzazione {sync.id}: {e}")
        
        print(f"Rimossi {past_events_removed} eventi passati")
        
        # -------------------------
        # FASE 4: SINCRONIZZAZIONE APPELLI
        # -------------------------
        
        # Ottieni gli appelli con filtri
        appelli_query = AppelloEsame.objects.all()
        
        if facolta_id:
            appelli_query = appelli_query.filter(esame__facolta__id=facolta_id)
            
        if anno_esame:
            appelli_query = appelli_query.filter(esame__anno=int(anno_esame))
            
        if periodo_esame:
            appelli_query = appelli_query.filter(esame__semestre=int(periodo_esame))
        
        appelli_count = appelli_query.count()
        print(f"Trovati {appelli_count} appelli totali con i filtri applicati")
        
        # Filtra solo appelli futuri o di oggi
        future_appelli = []
        for appello in appelli_query:
            try:
                # Estrai data appello
                date_str = appello.data.split(" - ")[0] if " - " in appello.data else appello.data.split()[0]
                day, month, year = map(int, date_str.split('/'))
                appello_date = datetime(year, month, day).date()
                
                if appello_date >= today.date():
                    future_appelli.append(appello)
            except Exception as e:
                print(f"Errore nel parsing della data dell'appello {appello.id}: {e}")
        
        print(f"Trovati {len(future_appelli)} appelli futuri o di oggi")
        
        # Contatori per statistiche
        events_created = 0
        events_updated = 0
        events_skipped = 0
        
        # Processa ogni appello futuro
        for idx, appello in enumerate(future_appelli[:100]):  # Limita a 100 per sicurezza
            print(f"Elaborazione appello {idx+1}/{len(future_appelli)}: {appello.esame.nome}")
            
            try:
                # 1. Verifica se esiste già una sincronizzazione nel DB
                existing_sync = CalendarSync.objects.filter(user=request.user, appello=appello).first()
                
                if existing_sync:
                    print(f"Trovata sincronizzazione esistente con ID: {existing_sync.google_event_id}")
                    
                    # Verifica se l'evento esiste ancora su Google Calendar
                    try:
                        event = service.events().get(calendarId='primary', eventId=existing_sync.google_event_id).execute()
                        print(f"Evento trovato in Google Calendar, aggiornamento...")
                        
                        # Aggiorna l'evento esistente
                        try:
                            from .autosync import update_google_calendar_event
                            update_google_calendar_event(existing_sync)
                            events_updated += 1
                            print(f"Evento aggiornato con successo")
                        except Exception as e:
                            print(f"Errore nell'aggiornamento dell'evento: {e}")
                        continue
                        
                    except Exception as e:
                        if "404" in str(e):
                            print("Evento non trovato in Google Calendar, verrà ricreato")
                            # L'evento non esiste più, elimina il record e crea un nuovo evento
                            existing_sync.delete()
                        else:
                            print(f"Errore nel controllo dell'evento: {e}")
                            events_skipped += 1
                            continue
                
                # 2. Estrai data e ora
                date_str = appello.data.split(" - ")[0] if " - " in appello.data else appello.data.split()[0]
                time_str = appello.data.split(" - ")[1] if " - " in appello.data else "09:00"
                
                day, month, year = map(int, date_str.split('/'))
                
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                else:
                    hour, minute = 9, 0
                
                start_time = datetime(year, month, day, hour, minute)
                end_time = start_time + timedelta(hours=2)
                
                # 3. Controlla se già esiste un evento con questo titolo e data
                event_title = appello.esame.nome
                start_date = datetime(year, month, day, 0, 0, 0).isoformat() + 'Z'
                end_date = datetime(year, month, day, 23, 59, 59).isoformat() + 'Z'
                
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=start_date,
                    timeMax=end_date,
                    q=event_title,
                    singleEvents=True
                ).execute()
                
                matching_events = []
                for event in events_result.get('items', []):
                    if event.get('summary') == event_title:
                        matching_events.append(event)
                
                if matching_events:
                    print(f"Trovati {len(matching_events)} eventi esistenti con lo stesso titolo e data")
                    
                    # Verifica se qualcuno di questi è già collegato nel DB
                    existing_ids = [e['id'] for e in matching_events]
                    db_syncs = CalendarSync.objects.filter(
                        user=request.user, 
                        google_event_id__in=existing_ids
                    )
                    
                    if db_syncs.exists():
                        # Evento già sincronizzato in precedenza
                        print(f"Appello già sincronizzato, aggiorno solo le informazioni")
                        sync = db_syncs.first()
                        try:
                            from .autosync import update_google_calendar_event
                            update_google_calendar_event(sync)
                            events_updated += 1
                        except Exception as e:
                            print(f"Errore nell'aggiornamento: {e}")
                    else:
                        # Elimina gli eventi duplicati e crea un record nel DB
                        # Conserva solo il primo evento, elimina gli altri
                        keep_event = matching_events[0]
                        
                        # Elimina eventuali altri eventi duplicati
                        for event in matching_events[1:]:
                            print(f"Elimino evento duplicato: {event['id']}")
                            service.events().delete(calendarId='primary', eventId=event['id']).execute()
                        
                        # Crea la sincronizzazione per l'evento esistente
                        CalendarSync.objects.create(
                            user=request.user,
                            appello=appello,
                            google_event_id=keep_event['id']
                        )
                        events_updated += 1
                        print(f"Creata associazione con evento esistente: {keep_event['id']}")
                    
                    continue
                
                # 4. Crea un nuovo evento
                print(f"Creazione nuovo evento per: {event_title}")
                
                # Determina il colore in base alla facoltà
                color_id = str(abs(hash(appello.esame.facolta.nome)) % 11 + 1)
                
                # Crea l'evento in Google Calendar
                event = {
                    'summary': event_title,
                    'location': f'Università di Modena e Reggio Emilia',
                    'description': f'Appello d\'esame per {appello.esame.nome}\nFacoltà: {appello.esame.facolta.nome}\nData e ora: {appello.data}',
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'Europe/Rome',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'Europe/Rome',
                    },
                    'colorId': color_id,
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 60},
                        ],
                    },
                }
                
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                print(f"Evento creato con ID: {created_event.get('id')}")
                
                # Salva relazione nel DB
                CalendarSync.objects.create(
                    user=request.user,
                    appello=appello,
                    google_event_id=created_event['id']
                )
                
                events_created += 1
                
            except Exception as e:
                print(f"Errore nell'elaborazione dell'appello {appello.id}: {e}")
                events_skipped += 1
        
        print(f"===== SINCRONIZZAZIONE COMPLETATA =====")
        print(f"Eventi creati: {events_created}")
        print(f"Eventi aggiornati: {events_updated}")
        print(f"Eventi saltati: {events_skipped}")
        print(f"Duplicati rimossi: {duplicates_removed}")
        print(f"Eventi passati rimossi: {past_events_removed}")
        
        # Reindirizza con parametri
        filter_params = ""
        if facolta_id:
            filter_params += f"&facolta_id={facolta_id}"
        if anno_esame:
            filter_params += f"&anno_esame={anno_esame}"
        if periodo_esame:
            filter_params += f"&periodo_esame={periodo_esame}"
        
        # Apri Google Calendar e reindirizza
        html = f"""
        <html>
        <head>
            <title>Sincronizzazione completata</title>
            <script>
                window.open('https://calendar.google.com/', '_blank');
                window.location.href = '/calendar/?sync_success=true&events_created={events_created}&events_updated={events_updated}&events_deleted={past_events_removed}{filter_params}';
            </script>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }}
                .card {{ max-width: 250px; margin: 0 auto; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                .success {{ color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1 class="success">Sincronizzazione completata!</h1>
                <p>Sono stati sincronizzati {events_created} appelli futuri.</p>
                <p>{events_updated} eventi esistenti sono stati aggiornati.</p>
                <p>{duplicates_removed + past_events_removed} eventi duplicati o passati sono stati rimossi.</p>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html)
        
    except Exception as e:
        print(f"Errore generale nella sincronizzazione: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Errore durante la sincronizzazione: {str(e)}")


@login_required
def sync_single_event(request, appello_id):
    """Sincronizza un singolo appello con Google Calendar, 
    gestendo correttamente i duplicati"""
    try:
        print(f"===== INIZIO SINCRONIZZAZIONE SINGOLO APPELLO {appello_id} =====")
        appello = get_object_or_404(AppelloEsame, id=appello_id)
        
        # Verifica se l'appello è nel futuro o oggi
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Estrai data appello
        date_str = appello.data.split(" - ")[0] if " - " in appello.data else appello.data.split()[0]
        day, month, year = map(int, date_str.split('/'))
        appello_date = datetime(year, month, day).date()
        
        # Se l'appello è già passato, non sincronizzare
        if appello_date < today.date():
            messages.warning(request, f"L'appello '{appello.esame.nome}' è una data passata e non verrà sincronizzato")
            return redirect(request.META.get('HTTP_REFERER', '/calendar/'))
        
        # Ottieni credenziali Google
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            social_token = SocialToken.objects.get(account=social_account)
                
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
            
            # Inizializza servizio Calendar
            service = build('calendar', 'v3', credentials=credentials)
            
        except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist):
            messages.error(request, "È necessario autorizzare Google Calendar prima")
            return redirect('start_google_auth')
        
        # Verifica se esiste già una sincronizzazione nel DB
        existing_sync = CalendarSync.objects.filter(user=request.user, appello=appello).first()
        
        if existing_sync:
            print(f"Trovata sincronizzazione esistente: {existing_sync.google_event_id}")
            
            # Verifica se l'evento esiste ancora in Google Calendar
            try:
                event = service.events().get(calendarId='primary', eventId=existing_sync.google_event_id).execute()
                print("Evento trovato in Google Calendar, aggiornamento...")
                
                # Aggiorna l'evento esistente
                try:
                    from .autosync import update_google_calendar_event
                    update_google_calendar_event(existing_sync)
                    messages.success(request, f"L'appello '{appello.esame.nome}' è stato aggiornato su Google Calendar")
                    return redirect(request.META.get('HTTP_REFERER', '/calendar/'))
                except Exception as e:
                    print(f"Errore nell'aggiornamento: {e}")
                    messages.error(request, f"Errore nell'aggiornamento dell'evento: {e}")
                    return redirect('/calendar/')
                    
            except Exception as e:
                if "404" in str(e):
                    print("Evento non trovato in Google Calendar, verrà ricreato")
                    # L'evento non esiste più, elimina il record
                    existing_sync.delete()
                else:
                    print(f"Errore nel controllo dell'evento: {e}")
                    messages.error(request, f"Errore nella verifica dell'evento: {e}")
                    return redirect('/calendar/')
        
        # Controlla se esistono eventi duplicati in Google Calendar
        event_title = appello.esame.nome
        
        start_date = datetime(year, month, day, 0, 0, 0).isoformat() + 'Z'
        end_date = datetime(year, month, day, 23, 59, 59).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_date,
            timeMax=end_date,
            q=event_title,
            singleEvents=True
        ).execute()
        
        matching_events = []
        for event in events_result.get('items', []):
            if event.get('summary') == event_title:
                matching_events.append(event)
        
        if matching_events:
            print(f"Trovati {len(matching_events)} eventi esistenti con lo stesso titolo e data")
            
            # Elimina eventuali duplicati
            if len(matching_events) > 1:
                for event in matching_events[1:]:
                    print(f"Elimino evento duplicato: {event['id']}")
                    service.events().delete(calendarId='primary', eventId=event['id']).execute()
            
            # Usa il primo evento e crea la sincronizzazione
            keep_event = matching_events[0]
            
            # Verifica se esiste già una sincronizzazione per questo evento
            existing = CalendarSync.objects.filter(google_event_id=keep_event['id']).first()
            if existing:
                if existing.appello_id != appello.id:
                    # L'evento è associato a un altro appello, aggiorna il riferimento
                    existing.appello = appello
                    existing.save()
                    messages.success(request, f"L'appello '{appello.esame.nome}' è stato associato a un evento esistente su Google Calendar")
                else:
                    messages.info(request, f"L'appello '{appello.esame.nome}' è già sincronizzato con Google Calendar")
            else:
                # Crea una nuova sincronizzazione con l'evento esistente
                CalendarSync.objects.create(
                    user=request.user,
                    appello=appello,
                    google_event_id=keep_event['id']
                )
                messages.success(request, f"L'appello '{appello.esame.nome}' è stato associato a un evento esistente su Google Calendar")
            
            return redirect(request.META.get('HTTP_REFERER', '/calendar/'))
        
        # Se non esistono duplicati, crea un nuovo evento
        print(f"Creazione nuovo evento per: {event_title}")
        
        # Estrai ora
        time_str = appello.data.split(" - ")[1] if " - " in appello.data else "09:00"
        
        if ':' in time_str:
            hour, minute = map(int, time_str.split(':'))
        else:
            hour, minute = 9, 0
        
        start_time = datetime(year, month, day, hour, minute)
        end_time = start_time + timedelta(hours=2)
        
        # Determina il colore in base alla facoltà
        color_id = str(abs(hash(appello.esame.facolta.nome)) % 11 + 1)
        
        # Crea l'evento in Google Calendar
        event = {
            'summary': event_title,
            'location': f'Università di Modena e Reggio Emilia',
            'description': f'Appello d\'esame per {appello.esame.nome}\nFacoltà: {appello.esame.facolta.nome}\nData e ora: {appello.data}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Rome',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Rome',
            },
            'colorId': color_id,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Evento creato con ID: {created_event.get('id')}")
        
        # Salva relazione nel DB
        CalendarSync.objects.create(
            user=request.user,
            appello=appello,
            google_event_id=created_event['id']
        )
        
        messages.success(request, f"L'appello '{appello.esame.nome}' è stato sincronizzato con Google Calendar")
        return redirect(request.META.get('HTTP_REFERER', '/calendar/'))
            
    except Exception as e:
        print(f"Errore generale: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Errore durante la sincronizzazione: {e}")
        return redirect('/calendar/')
    
def clean_past_calendar_events():
    """Elimina automaticamente gli eventi del calendario passati per tutti gli utenti"""
    try:
        print("===== INIZIO PULIZIA AUTOMATICA EVENTI PASSATI =====")
        
        # Ottieni la data di oggi
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        events_deleted = 0
        
        # Trova tutti gli utenti che hanno sincronizzazioni
        user_ids = CalendarSync.objects.values_list('user_id', flat=True).distinct()
        print(f"Trovati {len(user_ids)} utenti con sincronizzazioni")
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                print(f"Elaborazione utente: {user.username}")
                
                # Ottieni credenziali
                try:
                    social_account = SocialAccount.objects.get(user=user, provider='google')
                    social_token = SocialToken.objects.get(account=social_account)
                    
                    credentials = Credentials(
                        token=social_token.token,
                        refresh_token=social_token.token_secret,
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                        client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
                    )
                    
                    # Inizializza servizio Calendar
                    service = build('calendar', 'v3', credentials=credentials)
                    
                except Exception as e:
                    print(f"Errore nell'ottenere le credenziali per l'utente {user.username}: {e}")
                    continue
                
                # Trova sincronizzazioni per questo utente
                syncs = CalendarSync.objects.filter(user=user)
                
                for sync in syncs:
                    try:
                        # Estrai data appello
                        date_str = sync.appello.data.split(" - ")[0] if " - " in sync.appello.data else sync.appello.data.split()[0]
                        day, month, year = map(int, date_str.split('/'))
                        appello_date = datetime(year, month, day).date()
                        
                        # Se l'appello è passato, rimuovi
                        if appello_date < today.date():
                            try:
                                print(f"Rimozione evento passato: {sync.appello.esame.nome} del {date_str}")
                                service.events().delete(calendarId='primary', eventId=sync.google_event_id).execute()
                                sync.delete()
                                events_deleted += 1
                            except Exception as e:
                                if "404" in str(e):
                                    # Se l'evento non esiste più, rimuovi solo il record
                                    sync.delete()
                                    events_deleted += 1
                                else:
                                    print(f"Errore nella rimozione dell'evento: {e}")
                    except Exception as e:
                        print(f"Errore nell'elaborazione della sincronizzazione {sync.id}: {e}")
                
            except Exception as e:
                print(f"Errore generale per l'utente {user_id}: {e}")
        
        print(f"===== PULIZIA COMPLETATA =====")
        print(f"Eventi passati eliminati: {events_deleted}")
        return events_deleted
        
    except Exception as e:
        print(f"Errore generale nella pulizia: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0