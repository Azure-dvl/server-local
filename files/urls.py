from django.urls import path

from . import views

urlpatterns = [
    path('', views.FileListView.as_view(), name='files.index'),
    path('download/<int:id>/', views.download, name='download'),
    path('stream/<int:id>/', views.stream_file, name='stream_file'),
    path('download-folder/<int:id>/', views.download_folder, name='download_folder'),
]