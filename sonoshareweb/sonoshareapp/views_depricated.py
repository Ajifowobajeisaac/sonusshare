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
        playlist_url = request.POST.get('playlist_url')
        
        if 'spotify.com' in playlist_url:
            try:
                playlist_id = extract_playlist_id(playlist_url, 'spotify')
                playlist = get_spotify_playlist(request, playlist_id)
                track_info = extract_track_info(playlist['tracks']['items'], 'spotify')
                
                for track in track_info:
                    track['apple_music_id'] = search_track_on_apple_music(request, track['name'], track['artist'])
                
                return create_apple_music_playlist(
                    playlist['name'],
                    playlist['description'],
                    [track['apple_music_id'] for track in track_info if track['apple_music_id']]
                )
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        elif 'music.apple.com' in playlist_url:
            try:
                print("Extracting playlist ID from Apple Music URL")
                playlist_id = extract_playlist_id(playlist_url, 'apple_music')
                print(f"Extracted playlist ID: {playlist_id}")

                print("Fetching Apple Music playlist")
                playlist = get_apple_music_playlist(request, playlist_id)
                print("Apple Music playlist fetched successfully")

                print("Extracting track info from Apple Music playlist")
                track_info = extract_track_info(playlist['data'][0]['relationships']['tracks']['data'], 'apple_music')
                print(f"Extracted track info: {track_info}")
                

                spotify_track_ids = search_tracks_on_spotify(track_info)
                spotify_tracks = {}
                for track in track_info:
                    # print(f"Searching for track on Spotify: {track['name']} by {track['artist']}")
                    spotify_tracks.update({track['name'] : track['artist']})

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
                
                print("Creating Spotify playlist")
                return JsonResponse({
                    'playlist_name': playlist['data'][0]['attributes']['name'],
                    'playlist_description': playlist_description,
                    'track_ids': spotify_track_ids,
                    'track_info': track_info,
                    'status': 'success'
                })
            except spotipy.SpotifyException as e:
                if e.http_status == 429:
                    error_message = "Spotify API rate limit exceeded. Please try again later."
                    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})
                else:
                    print(f"Error occurred: {str(e)}")
                    return JsonResponse({'error': str(e)}, status=500)
            except AttributeError as e:
                print(f"AttributeError occurred: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
        else:
            print("Invalid playlist URL")
            return JsonResponse({'error': 'Invalid playlist URL'}, status=400)
    
    else:
        print("Request method is not POST. Redirecting to index.")
        return redirect('index')


# Apple Music API functions
def get_apple_music_playlist(request, playlist_id):
    print(f"get_apple_music_playlist called with playlist_id: {playlist_id}")
    url = f'https://api.music.apple.com/v1/catalog/gb/playlists/{playlist_id}'
    headers = {
        'Authorization': f'Bearer {APPLE_MUSIC_TOKEN}',
    }
    print(f"Making request to URL: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Response status code is 200. Returning response JSON.")
        return response.json()
    elif response.status_code == 404:
        print("Response status code is 404. Playlist not found.")
        error_data = response.json()
        error_message = error_data.get('errors', [{}])[0].get('detail', 'Playlist not found')
        raise Exception(error_message)
    else:
        raise Exception(f'Error retrieving Apple Music playlist: {response.text}')

def create_apple_music_playlist(request, name, description, track_ids):
    url = 'https://api.music.apple.com/v1/me/library/playlists'
    headers = {
        'Authorization': f'Bearer {APPLE_MUSIC_TOKEN}',
        'Music-User-Token': request.session.get('apple_music_user_token', '')
    }
    data = {
        'attributes': {
            'name': name,
            'description': description
        },
        'relationships': {
            'tracks': {
                'data': [{'id': track_id, 'type': 'songs'} for track_id in track_ids]
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f'Error creating Apple Music playlist: {response.text}')
    
def search_track_on_apple_music(track_name, artist_name):
    url = f'https://api.music.apple.com/v1/catalog/us/search?types=songs&term={track_name}+{artist_name}'
    headers = {
        'Authorization': f'Bearer {APPLE_MUSIC_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        results = response.json()
        if results['results']['songs']['data']:
            return results['results']['songs']['data'][0]['id']
    return None

# Spotify API functions
def get_spotify_playlist(request, playlist_id):
    sp = spotipy.Spotify(auth=get_spotify_token(request))
    return sp.playlist(playlist_id)

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
    # Obtain an access token using the Client Credentials flow
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    auth_response = requests.post(auth_url, data=auth_data)
    
    if auth_response.status_code == 200:
        access_token = auth_response.json().get('access_token')
    else:
        print(f"Error obtaining access token: {auth_response.text}")
        return None
    
    # Use the access token to search for the track
    url = 'https://api.spotify.com/v1/search'
    params = {
        'q': f'track:{track_name} artist:{artist_name}',
        'type': 'track',
        'limit': 1
    }
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        if results['tracks']['items']:
            return results['tracks']['items'][0]['id']
    else:
        print(f"Error searching for track: {response.text}")
    
    return None


 

# Utility functions
def extract_playlist_id(playlist_url, platform):
    if platform == 'spotify':
        pattern = re.compile(r'playlist/([a-zA-Z0-9_-]+)')
    elif platform == 'apple_music':
        pattern = re.compile(r'pl\.([a-zA-Z0-9_-]+)')
    else:
        return None

    match = pattern.search(playlist_url)
    if match:
        if platform == 'apple_music':
            return f"pl.{match.group(1)}"  # Include the 'pl.' prefix for Apple Music
        else:
            return match.group(1)
    else:
        return None

def extract_track_info(tracks, platform):
    track_info = []
    for track in tracks:
        if platform == 'spotify':
            track_info.append({
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name'],
                'spotify_id': track['track']['id'],
                'apple_music_id': None  # You'll need to search for the track on Apple Music and get its ID
            })
        elif platform == 'apple_music':
            track_info.append({
                'name': track['attributes']['name'],
                'artist': track['attributes']['artistName'],
                'apple_music_id': track['id'],
                'spotify_id': None  # You'll need to search for the track on Spotify and get its ID
            })
    return track_info

def error(request):
    error_message = request.GET.get('error_message', 'An unknown error occurred.')
    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})
