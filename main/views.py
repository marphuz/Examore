from allauth.socialaccount.models import SocialAccount, SocialToken
from django.shortcuts import render, redirect, get_object_or_404
from .forms import LoginForm, RegisterForm
from django.contrib.auth import login, authenticate
from .utils import create_google_calendar_event
from scraping_creatingmodels import create, scraping
from .models import Facolta,Esame,AppelloEsame,Aula, DisponibilitaOraria
from datetime import datetime, date


# Create your views here.
def home(request):
    return render(request, "main/base.html", {})


def esami(request):
    facolta = Facolta.objects.all()
    return render(request, "main/esami.html", {"facolta": facolta})


def esami_per_facolta(request, facolta_id):
    facolta = get_object_or_404(Facolta, id=facolta_id)
    exams = Esame.objects.filter(facolta=facolta)
    context = {
        'facolta': facolta,
        'esami': exams,
    }
    return render(request, 'main/esami_per_facolta.html', context)


def calendar(request, facolta_id=None, day=None, month=None, year=None):
    aule = Aula.objects.all()
    if day is None and month is None and year is None:
        today = datetime.today()
        day = today.strftime("%d")
        month = today.strftime("%m")
        year = today.strftime("%Y")

    data_attuale = date(int(year), int(month), int(day))

    aule_disponibilita = {}

    for a in aule:
        aule_disponibilita[a] = DisponibilitaOraria.objects.filter(aula=a, data=data_attuale)

    context = {
        "aule": aule,
        "data_attuale": data_attuale,
        "aule_disponibilita": aule_disponibilita
    }
    return render(request, "main/cl.html", context)


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
