from . import scraping
from main.models import Facolta, Esame, AppelloEsame, Aula, DisponibilitaOraria
from django.core.management import call_command
from django.db import connection
from selenium.common import TimeoutException
from datetime import datetime, date
from django.core.exceptions import ObjectDoesNotExist


def createFacolta():
    facolta = scraping.getFacoltafromAppelli()
    for f in facolta:
        Facolta.objects.create(nome=f, durata=facolta[f])


def createEsami(year=None, index=None):
    facolta = Facolta.objects.all()
    j = index if index is not None else 0
    while j < len(facolta):
        cod = scraping.getFacultyCod(facolta[j].nome)
        try:
            result = scraping.getExamsInformation(cod, year)
            for i in range(len(result[0])):
                Esame.objects.get_or_create(
                    nome=result[0][i],
                    anno=int(result[1][i]),
                    crediti=result[2][i],
                    semestre=result[3][i],
                    facolta=facolta[j]
                )

        except TimeoutException:
            Esame.objects.filter(facolta=facolta[j]).delete()
            createEsami(year, index=j)
            break
        j += 1


def createAppelli(index=None):
    facolta = Facolta.objects.all()
    j = index if index is not None else 0
    while j < len(facolta):
        try:
            result = scraping.getAppelliInformation(facolta[j].nome)
            for i in range(len(result[0])):
                try:
                    ex = Esame.objects.get(nome=result[0][i], facolta=facolta[j])
                    AppelloEsame.objects.get_or_create(
                        data=result[1][i],
                        esame=ex
                    )
                except ObjectDoesNotExist:
                    continue
        except TimeoutException:
            AppelloEsame.objects.filter(esame__facolta=facolta[j]).delete()
            createAppelli(j)
            break
        j += 1


def createAule():
    aule_list = scraping.getAule()
    for a in aule_list:
        Aula.objects.get_or_create(nome=a)


def createDisponibilitaOraria(aule_disponibilita, data):
    aule = Aula.objects.all()
    for a in aule:
        list_disp = aule_disponibilita.get(a.nome)
        for d in list_disp:
            DisponibilitaOraria.objects.get_or_create(
                aula=a,
                data=data,
                ora_inizio=d[:5],
                ora_fine=d[6:11]
            )


def createAuleDisponibilita(day=None, month=None, year=None):
    if day is None and month is None and year is None:
        today = datetime.today()
        day = today.strftime("%d")
        month = today.strftime("%m")
        year = today.strftime("%Y")

    aule_disponibilita = scraping.getAuleInformation(day, month, year)
    data = date(int(year), int(month), int(day))
    createDisponibilitaOraria(aule_disponibilita, data)




def deleteDB():
    DisponibilitaOraria.objects.all().delete()
    Aula.objects.all().delete()
    AppelloEsame.objects.all().delete()
    Esame.objects.all().delete()
    Facolta.objects.all().delete()


def resetDB(old_facolta, old_esami, old_appelli, old_aule, old_disp):
    for facolta in old_facolta:
        facolta.pk = None
        facolta.save()

    for esame in old_esami:
        esame.pk = None
        esame.save()

    for appello in old_appelli:
        appello.pk = None
        appello.save()

    for aula in old_aule:
        aula.pk = None
        aula.save()

    for disp in old_disp:
        disp.pk = None
        disp.save()


def updateDB():
    old_facolta = list(Facolta.objects.all())
    old_esami = list(Esame.objects.all())
    old_appelli = list(AppelloEsame.objects.all())
    old_aule = list(Aula.objects.all())
    old_disp = list(DisponibilitaOraria.objects.all())

    try:
        deleteDB()
        createFacolta()
        createEsami()
        createAppelli()
        createAule()
        createAuleDisponibilita()
    except Exception as e:
        print(e)
        resetDB(old_facolta, old_esami, old_appelli, old_aule, old_disp)


def main():
    try:
        updateDB()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
