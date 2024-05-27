# views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Song
from .tasks import convert_playlist_
import json




def index(request):
    return render(request, 'sonoshareapp/index.html')

def convert_playlist(request):

    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        task = convert_playlist_.delay(playlist_url)
        return JsonResponse({'task_id': task.task_id})
    else:
        return redirect('index')
    
def review_playlist(request):
    data = json.loads(request.GET.get('data', '{}'))
    return render(request, 'sonoshareapp/review_playlist.html', data)

def error(request):
    error_message = request.GET.get('error_message', 'An unknown error occurred.')
    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})
