# main/tasks.py

from .autosync import sync_appelli_changes

from .views import clean_past_calendar_events

def run_sync_task():
    try:
        # Sincronizza appelli modificati
        sync_appelli_changes()
        # Esegui pulizia eventi passati
        clean_past_calendar_events()
        print("Sincronizzazione e pulizia completate con successo")
    except Exception as e:
        print(f"Errore durante la sincronizzazione automatica: {e}")

