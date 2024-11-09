from allauth.socialaccount.models import SocialAccount, SocialToken
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import LoginForm, RegisterForm
from django.contrib.auth import login, authenticate
from .utils import create_google_calendar_event
from scraping_creatingmodels import create, scraping
from .models import Facolta, Esame, AppelloEsame, Aula, DisponibilitaOraria
from datetime import datetime, date
from types import NoneType
import re

#COSTANTI:
DAY_SELECTED = None
MONTH_SELECTED = None
YEAR_SELECTED = None

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
    global DAY_SELECTED, MONTH_SELECTED, YEAR_SELECTED
    aule = Aula.objects.all()
    aule_select_filter = Aula.objects.all()
    aule_disponibilita = {}
    anno_esame = request.POST.get('anno_esame')
    periodo_esame = request.POST.get('periodo_esame')
    aula_visible = request.POST.get('aula_visible')
    disp_input = request.POST.get('disp-input')
    facolta_id = request.GET.get('facolta_id')
    real_facolta_id = None
    if facolta_id is not None:
        real_facolta_id = facolta_id

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
        appelli_attuali = filterAppelli(anno_esame, periodo_esame, data_stringa, facolta_id)

        if aula_visible:
            aule = Aula.objects.filter(nome=aula_visible)

        for aula in aule:
            disp = DisponibilitaOraria.objects.filter(aula=aula, data=data_attuale)
            aule_disponibilita[aula.nome] = [{"ora_inizio": d.ora_inizio, "ora_fine": d.ora_fine} for d in
                                             disp] if disp else "No disp."

            # Risposta JSON per AJAX
        return JsonResponse({
            "appelli": [
                {
                    "esame": appello.esame.nome,
                    "data": appello.data
                } for appello in appelli_attuali
            ],
            "aule_disponibilita": aule_disponibilita,
            "data_attuale": data_stringa,
            "anno_esame": anno_esame,
            "periodo_esame": periodo_esame,

        })
    else:
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
            "aule_select_filter": aule_select_filter,
            "day_selected": DAY_SELECTED,
            "month_selected": MONTH_SELECTED,
            "year_selected": YEAR_SELECTED,
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
