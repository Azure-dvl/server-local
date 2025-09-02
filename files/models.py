import os
from django.db import models

# Create your models here.
class Server(models.Model):
    ip = models.CharField(max_length=15)
    port = models.IntegerField(default=80)

    def __str__(self):
        return f"{self.ip}"

class File(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    is_folder = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    last_modified = models.FloatField(default=0.0)
    path = models.CharField(max_length=2048, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)  # Asegurar null=True, blank=True
    is_video = models.BooleanField(default=False)
    mime_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        # Determinar si es video y el tipo MIME
        if not self.is_folder and self.name:
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
            file_ext = os.path.splitext(self.name)[1].lower()
            self.is_video = file_ext in video_extensions
            
            # Determinar tipo MIME
            import mimetypes
            self.mime_type = mimetypes.guess_type(self.name)[0]
        
        super().save(*args, **kwargs)