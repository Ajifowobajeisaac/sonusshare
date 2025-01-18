"""
URL configuration for sonoshareweb project.

"""
from django.contrib import admin
from django.urls import include, path
from sonoshareapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sonoshareapp.urls')),
    path('spotify/auth/', views.spotify_auth, name='spotify_auth'),
    path('callback/', views.spotify_callback_view, name='spotify_callback'),
    path('celery-progress/', include('celery_progress.urls')),
]
