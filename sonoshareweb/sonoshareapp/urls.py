from django.urls import path
from .views import test_create_song

urlpatterns = [
    path('test-create-song/', test_create_song, name='test_create_song'),
]
