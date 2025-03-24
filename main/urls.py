from django.urls import path, include
from . import views as main_view
from django.contrib.auth import views as auth_views
from django.urls import path


# NEL CASO IL LOGIN CON GOOGLE NON FUNZIONI REINSERIRE QUESTO NEL PATH('accounts/')
# "django.contrib.auth.urls"

urlpatterns = [
    path('', main_view.home, name="home"),
    path('esami/', main_view.esami, name="esami"),
    path('calendar/', main_view.calendar, name="calendar"),
    path('login/', main_view.login_view, name="login"),
    path('accounts/', include("allauth.urls")),
    path('register/', main_view.register_view, name="register"),
    path('logout/', auth_views.LogoutView.as_view(template_name='main/registration/logout.html'), name="logout"),
    path('scraping/', main_view.scrapingOnDemand, name='scrapingOnDemand'),
    path('sync_and_open_gcal/', main_view.start_google_auth, name='sync_and_open_gcal'),
    path('start_google_auth/', main_view.start_google_auth, name='start_google_auth'),
    path('handle_google_token/', main_view.handle_google_token, name='handle_google_token'),
    path('sync_calendar_and_redirect/', main_view.sync_calendar_and_redirect, name='sync_calendar_and_redirect'),
    path('sync_single_event/<int:appello_id>/', main_view.sync_single_event, name='sync_single_event'),
]
