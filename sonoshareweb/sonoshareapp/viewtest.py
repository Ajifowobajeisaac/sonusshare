from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Song
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import re
import json
import requests
import base64
import hashlib
import os
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

SPOTIFY_CLIENT_ID = '31e4302c101d4027ab0da2c6be1763ca'
SPOTIFY_CLIENT_SECRET = 'f78a7bde118241c0ae48493ff5bfe4ab'
SPOTIFY_REDIRECT_URI = 'http://localhost:3333/callback/'
SPOTIFY_SCOPE = 'playlist-read-private playlist-modify-public playlist-modify-private'

APPLE_MUSIC_TOKEN = 'eyJhbGciOiJFUzI1NiIsImtpZCI6IjI0N0NaMzJSQUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiI3MzJOMzhMN0FNIiwiaWF0IjoxNzE1NjY1NTI1LCJleHAiOjE3MzE0NDI1MjV9.mlMPZwvG6eSi4D9SmJW_EzHlsPQ9EkghnStWwX9NFnaZYGfVrCACXhGAlVlzoUocH23f_S7EAz5RlMfPlPXWKw'

def index(request):
    return render(request, 'sonoshareapp/index.html')

def convert_playlist(request):
    if request.method == 'POST':
        playlist_url = json.loads(request.body).get('playlist_url')
        
        if 'spotify.com' in playlist_url:
            try:
                playlist_id = extract_playlist_id(playlist_url, 'spotify')
                playlist = get_spotify_playlist(request, playlist_id)
                track_info = extract_track_info(playlist['tracks']['items'], 'spotify')
                
                for track in track_info:
                    track['apple_music_id'] = search_track_on_apple_music(track['name'], track['artist'])
                
                return JsonResponse({
                    'playlist_name': playlist['name'],
                    'playlist_description': playlist['description'],
                    'track_ids': [track['apple_music_id'] for track in track_info if track['apple_music_id']],
                    'track_info': track_info,
                    'status': 'success'
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        elif 'music.apple.com' in playlist_url:
            try:
                playlist_id = extract_playlist_id(playlist_url, 'apple_music')
                playlist = get_apple_music_playlist(request, playlist_id)
                track_info = extract_track_info(playlist['data'][0]['relationships']['tracks']['data'], 'apple_music')
                
                spotify_track_ids = search_tracks_on_spotify(track_info)
                
                progress = {
                    'current_song': '',
                    'current_index': 0,
                    'total_songs': len(track_info)
                }
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'playlist_conversion',
                    {
                        'type': 'conversion_progress',
                        'message': progress
                    }
                )
                
                playlist_description = playlist['data'][0]['attributes'].get('description', {}).get('standard', '')
                
                return JsonResponse({
                    'playlist_name': playlist['data'][0]['attributes']['name'],
                    'playlist_description': playlist_description,
                    'track_ids': spotify_track_ids,
                    'track_info': track_info,
                    'status': 'success'
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'Invalid playlist URL'}, status=400)
    
    else:
        return redirect('index')

def create_spotify_playlist(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        track_ids = request.POST.get('track_ids').split(',')
        
        try:
            # Create Spotify playlist
            playlist_url = create_spotify_playlist_helper(request, name, description, track_ids)
            return JsonResponse({'status': 'success', 'playlist_url': playlist_url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    else:
        return redirect('index')

def create_spotify_playlist_helper(request, name, description, track_ids):
    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    redirect_uri = SPOTIFY_REDIRECT_URI
    scope = 'playlist-modify-public playlist-modify-private'

    token = util.prompt_for_user_token(request.session.session_key, scope, client_id, client_secret, redirect_uri)

    if token:
        sp = spotipy.Spotify(auth=token)
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(user_id, name, description=description)
        sp.user_playlist_add_tracks(user_id, playlist['id'], track_ids)
        playlist_url = playlist['external_urls']['spotify']
        return playlist_url
    else:
        raise Exception("Failed to get Spotify access token")

# ... (Apple Music API functions and utility functions omitted for brevity) ...

def search_tracks_on_spotify(track_info):
    track_ids = []
    for index, track in enumerate(track_info, start=1):
        track_name = track['name']
        artist_name = track['artist']
        spotify_id = search_track_on_spotify(track_name, artist_name)
        if spotify_id:
            track_ids.append(spotify_id)
        
        # Update progress information
        progress = {
            'current_song': track_name,
            'current_index': index,
            'total_songs': len(track_info)
        }
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'playlist_conversion',
            {
                'type': 'conversion_progress',
                'message': progress
            }
        )
    return track_ids

def search_track_on_spotify(track_name, artist_name):
    # ... (Spotify track search function implementation) ...

def error(request):
    error_message = request.GET.get('error_message', 'An unknown error occurred.')
    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})
