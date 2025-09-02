from django.shortcuts import render
from django.views.generic import TemplateView

from random import choice
from string import ascii_letters, digits
from datetime import datetime, timedelta

from .models import User


# Create your views here.
class UserAdministration(TemplateView):
    
    def get(self, request):
        users_list =  User.objects.all().order_by('id').reverse().values_list()
        return render(request, 'users/index.html', {'users': users_list})
    
    def post(self, request):
        while True:
            # Prevent to duplicate users
            try:
                username = ''
                for _ in range(8):
                    username += choice(ascii_letters.join(digits))

                # Use this if u wanna use the cuba tz, but it doesn't gonna be reflected
                # at DB (It uses utf by default)
                # expiration = datetime.now(ZoneInfo('Cuba')) + timedelta(hours=1)
                expiration = datetime.now() + timedelta(hours=1, minutes=1)

                user = {
                    'username': username, 
                    'expiration': expiration
                }
                User(**user).save()
                break
            except:
                continue

        return render(request, 'users/index.html', {'users': User.objects.all().order_by('id').reverse().values_list()})