import json
import os
from django.core.management.base import BaseCommand
from catalogos.models import Catalogo

class Command(BaseCommand):
    help = 'Carga los catálogos desde archivos JSON'

    def handle(self, *args, **options):
        catalogos_data = {
            'novelas': 'novelas.json',
            'anime':'anime.json',
            'animados':'animados.json',
            'doramas':'doramas.json',
            'games':'games.json',
            'movies':'movies.json',
            'series':'series.json'
        }
        
        for type, archivo in catalogos_data.items():
            file_path = os.path.join(os.path.dirname(__file__), '../../../catalogos/json/', archivo)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                
                for item in datos:
                    Catalogo.objects.update_or_create(
                        name=item['name'],
                        type=type,
                        defaults={
                            'year': item.get('year'),
                            'size': item.get('size'),
                            'plataform': item.get('plataform'),
                            'seasons': item.get('seasons'),
                            'chapters': item.get('chapters'),
                            'synopsis': item.get('synopsis'),
                            'requirements': item.get('requirements'),
                            'photo': item.get('photo')
                        }
                    )
                
                self.stdout.write(f'✓ {len(datos)} items cargados para {type}')
                
            except FileNotFoundError:
                self.stderr.write(f'✗ Archivo no encontrado: {archivo}')
            except Exception as e:
                self.stderr.write(f'✗ Error procesando {archivo}: {e}')