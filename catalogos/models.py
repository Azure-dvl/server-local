from django.db import models

# Create your models here.
class Catalogo(models.Model):
    type = [
        ('games','Juegos'),
        ('anime', 'Anime'),
        ('series', 'Series'),
        ('movies', 'Peliculas'),
        ('animados', 'Animados'),
        ('novelas', 'Novelas'),
        ('doramas', 'Doramas')
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=type)
    year = models.IntegerField(null=True, blank=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    plataform = models.CharField(max_length=100, blank=True, null=True)
    seasons = models.CharField(max_length=50, blank=True, null=True)
    chapters = models.CharField(max_length=50, blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    photo = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        ordering=['name']
        unique_together = ['name', 'type']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"