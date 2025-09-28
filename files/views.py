from io import BytesIO
import mimetypes
import re
from shlex import quote
import time
import zipfile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.views.generic import TemplateView
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

import os, json

from python_casa import settings

from .models import File, Server
from users.models import User

# Create your views here.
class FileListView(TemplateView):
    
    def get(self, request):
        username = request.COOKIES.get('user')
        if not username:
            return redirect('index.index')
        user = User.objects.filter(username=username).first()
        if user.expiration < timezone.now():
            return redirect('index.index')
        
        parent_id = request.GET.get('file')
        current_folder = None
        breadcrumbs = []
        
        # Obtener la carpeta actual y construir breadcrumbs
        if parent_id:
            try:
                current_folder = File.objects.get(id=parent_id)
                # Construir breadcrumbs (ruta de navegación)
                breadcrumbs = self.get_breadcrumbs(current_folder)
            except File.DoesNotExist:
                pass
        
        # Obtener carpetas y archivos por separado
        folders = File.objects.filter(parent=parent_id, is_folder=True).order_by('name')
        files = File.objects.filter(parent=parent_id, is_folder=False).order_by('name')
        
        context = {
            'folders': folders,
            'files': files,
            'current_folder': current_folder,
            'breadcrumbs': breadcrumbs,
        }
        
        return render(request, 'files/index.html', context)
    
    def get_breadcrumbs(self, folder):
        """Construye la ruta de navegación (breadcrumbs) para la carpeta actual"""
        breadcrumbs = []
        current = folder
        
        while current:
            breadcrumbs.insert(0, {
                'name': current.name,
                'id': current.id
            })
            current = current.parent
        
        # Agregar la raíz al principio
        breadcrumbs.insert(0, {
            'name': 'Inicio',
            'id': None
        })
        
        return breadcrumbs
    
    def post(self, request):
        response = redirect('index.index')
        response.delete_cookie('user')
        return response
    
def download(request, id):
    file_obj = get_object_or_404(File, pk=id)
    file_path = file_obj.path
    
    if os.path.exists(file_path):
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
        return response
    else:
        raise Http404("File not Found")
    
def stream_file(request, id):
    """
    Endpoint para streaming de archivos de video
    """
    file_obj = get_object_or_404(File, pk=id)
    file_path = file_obj.path
    
    if not os.path.exists(file_path):
        raise Http404("El archivo no existe")
    
    # Configurar streaming
    file_size = os.path.getsize(file_path)
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d+)?', range_header) if range_header else None
    
    content_type = file_obj.mime_type or 'application/octet-stream'
    
    if range_match:
        # Streaming con rango (para seek)
        start_byte = int(range_match.group(1))
        end_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        
        if end_byte >= file_size:
            end_byte = file_size - 1
            
        length = end_byte - start_byte + 1
        
        with open(file_path, 'rb') as f:
            f.seek(start_byte)
            data = f.read(length)
        
        response = HttpResponse(
            data,
            status=206,
            content_type=content_type,
        )
        
        response['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
        response['Content-Length'] = str(length)
        response['Accept-Ranges'] = 'bytes'
    else:
        # Streaming completo
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = str(file_size)
    
    response['Content-Disposition'] = f'inline; filename="{quote(os.path.basename(file_path))}"'
    return response

def download_folder(request, id):
    """
    Endpoint para descargar carpetas completas como ZIP
    """
    folder = get_object_or_404(File, pk=id, is_folder=True)
    
    # Verificar si la carpeta ya tiene un ZIP generado (cache)
    zip_dir = os.path.join(settings.MEDIA_ROOT, 'zips')
    if not os.path.exists(zip_dir):
        os.makedirs(zip_dir)
    
    zip_path = os.path.join(zip_dir, f'{folder.id}.zip')
    
    # Si el ZIP existe y es reciente (menos de 1 hora), usarlo
    if os.path.exists(zip_path) and (time.time() - os.path.getmtime(zip_path)) < 3600:
        response = FileResponse(open(zip_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{quote(folder.name)}.zip"'
        return response
    
    # Si no existe o es viejo, crear uno nuevo
    # Usar un enfoque más eficiente para carpetas grandes
    from django.http import StreamingHttpResponse
    import tempfile
    
    # Crear un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_zip_path = tmp.name
    
    try:
        with zipfile.ZipFile(tmp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Función recursiva para agregar archivos al ZIP
            def add_files_to_zip(folder_id, base_path=""):
                items = File.objects.filter(parent_id=folder_id)
                for item in items:
                    if not item.is_folder and os.path.exists(item.path):
                        # Calcular la ruta relativa en el ZIP
                        arcname = os.path.join(base_path, item.name)
                        zip_file.write(item.path, arcname)
                    elif item.is_folder:
                        # Llamar recursivamente para subcarpetas
                        add_files_to_zip(item.id, os.path.join(base_path, item.name))
            
            # Comenzar desde la carpeta actual
            add_files_to_zip(folder.id, "")
        
        # Mover el archivo temporal a la ubicación de caché
        # if os.path.exists(zip_path):
        #     os.remove(zip_path)
        # os.rename(tmp_zip_path, zip_path)
        
        # Servir el archivo
        response = FileResponse(open(tmp_zip_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{quote(folder.name)}.zip"'
        return response
        
    except Exception as e:
        # Limpiar en caso de error
        if os.path.exists(tmp_zip_path):
            os.remove(tmp_zip_path)
        raise e
    
@csrf_exempt
def createFiles(request):
    if request.method != 'POST':
        return JsonResponse({})
    
    # Primero limpiar archivos huérfanos
    cleanup_orphaned_files()
    
    data = json.loads(request.body.decode('utf-8'))
    ip = data.get('server')
    server = Server.objects.filter(ip=ip).first()
    if not server:
        server = Server.objects.create(ip=ip)
    
    for file in data.get('files', []):
        __recursiveAddFileToDb(file, server)

    return JsonResponse({})

@csrf_exempt
def deleteFiles(request):
    if request.method != 'POST':
        return JsonResponse({})
    data = json.loads(request.body.decode('utf-8'))
    ip = data.get('server')
    server = Server.objects.filter(ip=ip).first()
    if not server:
        return JsonResponse({})
    File.objects.filter(server=server).delete()
    server.delete()
    return JsonResponse({})

def __recursiveAddFileToDb(file_data, server, parent=None):
    # Verificar si el archivo/carpeta ya existe
    existing_file = File.objects.filter(
        path=file_data.get('path'),
        server=server
    ).first()
    
    if existing_file:
        # Si existe, actualizarlo y establecer el parent correcto
        existing_file.name = file_data.get('name')
        existing_file.file_size = file_data.get('size', 0)
        existing_file.last_modified = file_data.get('last_modified', 0)
        existing_file.parent = parent
        existing_file.save()
        f = existing_file
    else:
        # Si no existe, crearlo
        f_dict = {
            "is_folder": file_data.get('type') == 'folder',
            "name": file_data.get('name'),
            "file_size": file_data.get('size', 0),
            "last_modified": file_data.get('last_modified', 0),
            "parent": parent,
            "path": file_data.get('path'),
            "server": server
        }
        f = File.objects.create(**f_dict)
    
    # Para carpetas, procesar archivos hijos
    if file_data.get('type') == 'folder':
        for _f in file_data.get('files', []):
            __recursiveAddFileToDb(_f, server, f)

def file_list(request):
    files = File.objects.values('id', 'path', 'file_size', 'last_modified')
    return JsonResponse(list(files), safe=False)

def cleanup_orphaned_files():
    """
    Elimina archivos de la base de datos que ya no existen en el sistema de archivos
    """
    all_files = File.objects.all()
    for file in all_files:
        if not os.path.exists(file.path):
            print(f"Eliminando archivo huérfano: {file.path}")
            file.delete()