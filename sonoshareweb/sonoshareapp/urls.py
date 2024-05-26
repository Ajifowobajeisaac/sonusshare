from django.urls import path, include
from . import views
from celery_progress import views as celery_progress_views
from .utils_spotify import create_spotify_playlist

urlpatterns = [
    path('', views.index, name='index'),
    path('convert_playlist/', views.convert_playlist, name='convert_playlist'),
    path('create_spotify_playlist/', create_spotify_playlist, name='create_spotify_playlist'),
    path('celery-progress/<str:task_id>/', celery_progress_views.get_progress, name='celery_progress:task_status'),
    path('celery-progress/', include('celery_progress.urls')),
    path('error/', views.error, name='error'),  
    path('progress/', views.progress, name='progress'),
    path('review_playlist/', views.review_playlist, name='review_playlist'),
]
