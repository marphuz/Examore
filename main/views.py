from allauth.socialaccount.models import SocialAccount, SocialToken
from django.shortcuts import render, redirect, get_object_or_404
from .forms import LoginForm, RegisterForm
from django.contrib.auth import login, authenticate
from .utils import create_google_calendar_event
from scraping_creatingmodels import create, scraping
from .models import Facolta, Esame, AppelloEsame, Aula, DisponibilitaOraria
from datetime import datetime, date
from types import NoneType
import re


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
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f, esame__anno=anno_esame)
        elif anno_esame == 0 and periodo_esame != 0:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f, esame__semestre=periodo_esame)
        else:
            appelli_attuali = AppelloEsame.objects.filter(data__icontains=data_stringa, esame__facolta=f, esame__anno=anno_esame,
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
    facolta_id = request.GET.get('facolta_id')
    real_facolta_id = None
    if facolta_id is not None:
        real_facolta_id = facolta_id
    aule = None
    aule_select_filter = Aula.objects.all()
    aule_disponibilita = {}
    anno_esame = request.GET.get('anno_esame')
    periodo_esame = request.GET.get('periodo_esame')
    aula_visible = request.POST.get('aula_visible')
    disp_input = request.POST.get('disp-input')

    day, month, year = checkDisp(disp_input)

    if aula_visible is None or aula_visible == "":
        aule = Aula.objects.all()
    else:
        aule = Aula.objects.filter(nome=aula_visible)

    if day is None and month is None and year is None:
        day = request.POST.get('day')
        month = request.POST.get('month')
        year = request.POST.get('year')
        if day is None and month is None and year is None:
            giorno_esame = request.GET.get('giorno_esame')
            if giorno_esame == "" or giorno_esame is None:
                today = datetime.today()
                day = today.strftime("%d")
                month = today.strftime("%m")
                year = today.strftime("%Y")
            else:
                date_object = datetime.strptime(giorno_esame, "%b. %d, %Y")
                day = date_object.day
                month = date_object.month
                year = date_object.year


    data_attuale = date(int(year), int(month), int(day))
    data_stringa = data_attuale.strftime("%d/%m/%Y")
    appelli_attuali = filterAppelli(anno_esame, periodo_esame, data_stringa, real_facolta_id)

    for a in aule:
        disp = DisponibilitaOraria.objects.filter(aula=a, data=data_attuale)
        if not disp:
            try:
                create.createAuleDisponibilita(day, month, year)
                disp = DisponibilitaOraria.objects.filter(aula=a, data=data_attuale)

            except:
                pass
        aule_disponibilita[a] = disp

    context = {
        "aule": aule,
        "data_attuale": data_attuale,
        "aule_disponibilita": aule_disponibilita,
        "appelli": appelli_attuali,
        "anno_esame": anno_esame,
        "periodo_esame": periodo_esame,
        "aule_select_filter": aule_select_filter
    }
    return render(request, "main/calendar.html", context)


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
