from django.db import models

# Create your models here.
ANNI = (
    (1, 'Primo Anno'),
    (2, 'Secondo Anno'),
    (3, 'Terzo Anno')
)

SEMESTRI = (
    (1, '1° Semestre'),
    (2, '2° Semestre'),
    (3, 'Ciclo Annuale Unico')
)




class Facolta(models.Model):
    nome = models.CharField(max_length=200)
    durata = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nome', 'durata'], name='unique_migration_nome_anno')
        ]

        def __str__(self):
            return self.nome


class Esame(models.Model):
    nome = models.CharField(max_length=100)
    anno = models.IntegerField(choices=ANNI)
    semestre = models.IntegerField(choices=SEMESTRI)
    crediti = models.CharField(max_length=10)
    facolta = models.ForeignKey(Facolta, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'anno', 'semestre', 'facolta'], name='unique_migration_Esame'
            )
        ]

    def __str__(self):
        return self.nome


class AppelloEsame(models.Model):
    data = models.CharField(max_length=19)
    esame = models.ForeignKey(Esame, on_delete=models.CASCADE)

    def __str__(self):
        return self.esame.nome + ' ' + str(self.data)


class Aula(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class DisponibilitaOraria(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    data = models.DateField()
    ora_inizio = models.CharField(max_length=6)
    ora_fine = models.CharField(max_length=6)

    class Meta:
        unique_together = ('aula', 'data', 'ora_inizio', 'ora_fine')