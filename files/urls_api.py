from django.urls import path

from . import views

urlpatterns = [
    path('create/', views.createFiles, name='files.create'),
    path('delete/', views.deleteFiles, name='files.delete'),
    path('list/', views.file_list, name='files.list'),
]