from django.urls import path

from . import views

urlpatterns = [
    path("", views.UserAdministration.as_view(), name="users.index"),
]