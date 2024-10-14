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

CREDITI = (
    (0, '0'),
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6'),
    (7, '7'),
    (8, '8'),
    (9, '9'),
    (10, '10'),
    (11, '11'),
    (12, '12'),
    (13, '13'),
    (14, '14'),
    (15, '15'),
    (16, '16'),
    (17, '17'),
    (18, '18'),
    (19, '19'),
    (20, '20'),
    (21, '21'),
    (22, '22'),
    (23, '23'),
    (24, '24'),
)

AULE = (
    (1, 'FA-2F'),
    (2, 'Fa-2g'),
    (3, 'FA-2E'),
)


class Facolta(models.Model):
    nome = models.CharField(max_length=200)
    anno = models.IntegerField(choices=ANNI)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nome', 'anno'], name='unique_migration_nome_anno')
        ]

        def __str__(self):
            return self.nome


class Esame(models.Model):
    nome = models.CharField(max_length=100)
    anno = models.IntegerField(choices=ANNI)
    semestre = models.IntegerField(choices=SEMESTRI)
    crediti = models.IntegerField(choices=CREDITI)
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
    data = models.DateTimeField()
    esame = models.ForeignKey(Esame, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['data', 'esame'], name='unique_migration_AppelloEsame'
            )
        ]

    def __str__(self):
        return self.esame.nome + ' ' + str(self.data)


class Aula(models.Model):
    nome = models.IntegerField(choices=AULE)
    data = models.DateTimeField()
    span_disponibilita = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['data', 'nome', 'span_disponibilita'], name='unique_migration_Aula'
            )
        ]

    def __str__(self):
        return self.nome + ' ' + self.span_disponibilita
