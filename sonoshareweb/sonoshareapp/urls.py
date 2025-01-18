from django.urls import path
from . import views
from .utils_spotify import spotify_auth, spotify_callback

urlpatterns = [
    path('', views.index, name='index'),
    path('review_playlist/', views.review_playlist, name='review_playlist'),
    path('convert_playlist/', views.convert_playlist, name='convert_playlist'),
    path('create_spotify_playlist/', views.create_spotify_playlist, name='create_spotify_playlist'),
    path('error/', views.error, name='error'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
