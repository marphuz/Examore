
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from allauth.socialaccount.models import SocialToken, SocialAccount
from datetime import datetime, timedelta

def get_credentials(user):
    try:
       
        social_account = SocialAccount.objects.get(user=user, provider='google')
        
        
        token = SocialToken.objects.get(account=social_account)
        
        credentials = Credentials(
            token=token.token,
            refresh_token=token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id='973528692771-7d4om4p64bmmbf6lnq23tt058agojjvf.apps.googleusercontent.com',
            client_secret='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',
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        return credentials
    except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist) as e:
        print(f"Error getting credentials: {e}")
        return None

def create_calendar_service(user):
    credentials = get_credentials(user)
    if not credentials:
        return None
    
    return build('calendar', 'v3', credentials=credentials)

def get_user_calendars(user):
    service = create_calendar_service(user)
    if not service:
        return []
    
    try:
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get('items', [])
    except Exception as e:
        print(f"Error getting calendars: {e}")
        return []

def create_examore_calendar(user):
    service = create_calendar_service(user)
    if not service:
        return None
    
    # Check if Examore calendar already exists
    calendars = get_user_calendars(user)
    for calendar in calendars:
        if calendar.get('summary') == 'Examore - Appelli d\'Esame':
            return calendar['id']
    
    # If not, create a new calendar
    calendar_body = {
        'summary': 'Examore - Appelli d\'Esame',
        'description': 'Calendario automatico degli appelli d\'esame da Examore',
        'timeZone': 'Europe/Rome'
    }
    
    try:
        created_calendar = service.calendars().insert(body=calendar_body).execute()
        return created_calendar['id']
    except Exception as e:
        print(f"Error creating calendar: {e}")
        return None

def add_exam_to_calendar(user, appello, calendar_id=None):
    service = create_calendar_service(user)
    if not service:
        return False
    
    # Get or create Examore calendar
    if not calendar_id:
        calendar_id = create_examore_calendar(user)
        if not calendar_id:
            return False
    

    try:
        start_datetime = datetime.strptime(appello.data, "%d/%m/%Y %H:%M")
        end_datetime = start_datetime + timedelta(hours=2)
    except ValueError:
        try:
            start_date = datetime.strptime(appello.data, "%d/%m/%Y")
            event = {
                'summary': f'Esame: {appello.esame.nome}',
                'description': f'Appello d\'esame per {appello.esame.nome} - {appello.esame.crediti} CFU',
                'start': {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'timeZone': 'Europe/Rome',
                },
                'end': {
                    'date': (start_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'timeZone': 'Europe/Rome',
                }
            }
        except ValueError:
            return False
    else:
        
        event = {
            'summary': f'Esame: {appello.esame.nome}',
            'description': f'Appello d\'esame per {appello.esame.nome} - {appello.esame.crediti} CFU',
            'start': {
                'dateTime': start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'Europe/Rome',
            },
            'end': {
                'dateTime': end_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'Europe/Rome',
            }
        }
    
    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event.get('id')
    except Exception as e:
        print(f"Error adding event to calendar: {e}")
        return False

def sync_all_exams(user, appelli):
    """Sync all exams to Google Calendar."""
    calendar_id = create_examore_calendar(user)
    if not calendar_id:
        return False
    
    success_count = 0
    for appello in appelli:
        if add_exam_to_calendar(user, appello, calendar_id):
            success_count += 1
    
    return success_count