from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('convert_playlist/', views.convert_playlist, name='convert_playlist'),
    path('create_spotify_playlist/', views.create_spotify_playlist, name='create_spotify_playlist'),
    path('error/', views.error, name='error'),  
]
