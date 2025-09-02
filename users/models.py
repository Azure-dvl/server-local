from django.db import models

# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=16, unique=True)
    expiration = models.DateTimeField() # Time of publication + 1 hour
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.username