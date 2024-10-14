from django.urls import path, include
from . import views as main_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', main_view.home, name="home"),
    path('esami/', main_view.esami, name="esami"),
    path('calendar/', main_view.calendar, name="calendar"),
    path('login/', main_view.login_view, name="login"),
    path('accounts/', include("django.contrib.auth.urls")),
    path('register/', main_view.register_view, name="register"),
    path('logout/', auth_views.LogoutView.as_view(template_name='main/registration/logout.html'), name="logout"),
]
