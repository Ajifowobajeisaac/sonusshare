from django.urls import path
from .views import create_user_playlist, index, convert_playlist

urlpatterns = [
    path('convert-playlist/', convert_playlist, name='convert_playlist'),
    path('create-user-playlist/', create_user_playlist, name='create_user_playlist'),
    path('', index, name='index'),
]
