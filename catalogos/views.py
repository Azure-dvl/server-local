from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .models import Catalogo

class CatalogoView(TemplateView):
    
    def get(self, request):
        return render(request, 'catalogos/index.html')
    
    
@csrf_exempt
def catalogos_api(request):
    if request.method == 'GET':
        type = request.GET.get('type', '')
        buscar = request.GET.get('buscar', '')
        
        catalogos = Catalogo.objects.all()
        
        if type:
            catalogos = catalogos.filter(type=type)
        
        if buscar:
            catalogos = catalogos.filter(nombre__icontains=buscar)
        
        data = list(catalogos.values(
            'name', 'type', 'year', 'size', 'plataform', 
            'seasons', 'chapters', 'synopsis', 'requirements', 'photo'
        ))
        
        return JsonResponse(data, safe=False)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)