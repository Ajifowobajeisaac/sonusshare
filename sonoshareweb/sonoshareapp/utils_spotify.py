# utils_spotify.py
from django.shortcuts import render, redirect
import requests
import urllib.parse
import time
from django.core.cache import cache

SPOTIFY_CLIENT_ID = 'a11e3bfb94954f4d94d150e090851e9c'
SPOTIFY_CLIENT_SECRET = 'b396b5e7d6c940a4a4d219a5bdcf3f07'
SPOTIFY_REDIRECT_URI = 'http://www.sonusshare.com/callback/'
SPOTIFY_SCOPE = 'playlist-read-private playlist-modify-private playlist-modify-public'

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# Spotify API functions
def get_spotify_playlist(request, playlist_id):
    pass

def spotify_auth(request):
    auth_params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SPOTIFY_SCOPE,
        'show_dialog': True
    }
    auth_url = f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    print("Redirecting to Spotify authentication page")
    return redirect(auth_url)

def spotify_callback(request):

    code = request.GET.get('code')
    print(f"Received code: {code}")  

    if code:
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        }
    else:
        raise Exception("No code returned")
    
    token_response = requests.post(SPOTIFY_TOKEN_URL, data=token_data)

    if token_response.status_code == 200:
        token_info = token_response.json()
        access_token = token_info['access_token']
        request.session['access_token'] = access_token
        return redirect('create_spotify_playlist')
    else:
        raise Exception("Failed to get Spotify access token")
    

def create_spotify_playlist(request):
    
    access_token = request.session.get('access_token')
    print(f"Access token from session: {access_token}")
    if not access_token:
        return redirect('spotify_auth')


    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        track_ids = request.POST.get('track_ids').split(',')

        user_response = requests.get(f"{API_BASE_URL}me", headers=headers)
        if user_response:            
            user_data = user_response.json()
            user_id = user_data['id']
        else:
            return render(request, 'sonoshareapp/register_email.html')




        playlist_data = {
            'name': name,
            'description': description,
            'public': False,
        }
        playlist_response = requests.post(f"{API_BASE_URL}users/{user_id}/playlists", headers=headers, json=playlist_data)
        if playlist_response:
            playlist_data = playlist_response.json()
            if 'id' in playlist_data:
                playlist_id = playlist_data['id']
            else:
                error_message = "Failed to create playlist"
                error_details = {
                    'status_code': playlist_response.status_code,
                    'response_text': playlist_response.text,
                    'error_message': error_message,
                }
                return render(request, 'sonoshareapp/error.html', {
                    'error_message': error_message,
                    'error_details': error_details,
                })
        else:
            raise Exception("No playlist response")

        try:
            add_tracks_response = requests.post(f"{API_BASE_URL}playlists/{playlist_id}/tracks", headers=headers, json={'uris': [f"spotify:track:{track_id}" for track_id in track_ids]})
        except Exception as e:
            print(f"Error searching for track on Spotify. Error: {str(e)}")

        playlist_url = playlist_data['external_urls']['spotify']
        return render(request, 'sonoshareapp/playlist_created.html', {
            'playlist_url': playlist_url,
        })
    else:
        print ("No request recieved")
        return render(request, 'sonoshareapp/index.html')

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
