
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
from django.shortcuts import render, redirect
import requests

SPOTIFY_CLIENT_ID = '31e4302c101d4027ab0da2c6be1763ca'
SPOTIFY_CLIENT_SECRET = 'f78a7bde118241c0ae48493ff5bfe4ab'
SPOTIFY_REDIRECT_URI = 'http://localhost:3333/callback/'
SPOTIFY_SCOPE = 'playlist-read-private playlist-modify-public playlist-modify-private'

# Spotify API functions
def get_spotify_playlist(request, playlist_id):
    sp = spotipy.Spotify(auth=get_spotify_token(request))
    return sp.playlist(playlist_id)

def create_spotify_playlist(request):
    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    redirect_uri = SPOTIFY_REDIRECT_URI
    scope = 'playlist-modify-public playlist-modify-private'

    token = util.prompt_for_user_token(request.session.session_key, scope, client_id, client_secret, redirect_uri)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        track_ids = request.POST.get('track_ids').split(',')
        

    if token:
        sp = spotipy.Spotify(auth=token)
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(user_id, name, description)
        sp.user_playlist_add_tracks(user_id, playlist['id'], track_ids)
        playlist_url = playlist['external_urls']['spotify']
        return render(request, 'sonoshareapp/playlist_created.html', {
            'playlist_url': playlist_url,
        })
    else:
        raise Exception("Failed to get Spotify access token")

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
