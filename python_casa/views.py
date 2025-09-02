from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.utils import timezone

from users.models import User

# Create your views here.
class IndexView(TemplateView):

    def get(self, request):
        return render(request, 'index/index.html')
    
    def post(self, request):
        user = User.objects.filter(username=request.POST['user']).first()
        if not user:
            return render(request, 'index/index.html', {'error': "User doesn't exists"})
        elif user.expiration < timezone.now():
            return render(request, 'index/index.html', {'error': "User haven't time"})
        elif user.is_active:
            return render(request, 'index/index.html', {'error': "User already logged in"})
        response = redirect('files.index')
        response.set_cookie('user', user.username)
        return response