from django.urls import path
from . import views

urlpatterns = [
    path("", views.CatalogoView.as_view(), name='catalogos'),
    path('api/', views.catalogos_api, name='catalogos_api'),
]