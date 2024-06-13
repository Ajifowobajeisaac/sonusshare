from django.urls import path, include
from . import views
from celery_progress import views as celery_progress_views
from .utils_spotify import create_spotify_playlist, spotify_auth, spotify_callback

urlpatterns = [
    path('', views.index, name='index'),
    path('convert_playlist/', views.convert_playlist, name='convert_playlist'),
    path('create_spotify_playlist/', create_spotify_playlist, name='create_spotify_playlist'),
    path('celery-progress/<str:task_id>/', celery_progress_views.get_progress, name='celery_progress:task_status'),
    path('celery-progress/', include('celery_progress.urls')),
    path('error/', views.error, name='error'),  
    path('progress/', views.progress, name='progress'),
    path('review_playlist/', views.review_playlist, name='review_playlist'),
    path('test_redis_connection/', views.test_redis_connection, name='test_redis_connection'),
    path('spotify_auth/', spotify_auth, name='spotify_auth'),
    path('callback/', spotify_callback, name='spotify_callback'),
    path('beta_testing/', views.beta_testing, name='beta_testing'),
    path('get_access/', views.get_access, name='get_access'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
