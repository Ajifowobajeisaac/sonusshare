# utils_spotify.py
from django.shortcuts import render, redirect
import requests
import urllib.parse
import time
from django.core.cache import cache
from functools import lru_cache
from django.conf import settings
import base64
import spotipy.util as util
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

logger = logging.getLogger(__name__)

SPOTIFY_CLIENT_ID = settings.SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET = settings.SPOTIFY_CLIENT_SECRET
SPOTIFY_REDIRECT_URI = settings.SPOTIFY_REDIRECT_URI
SPOTIFY_SCOPE = 'playlist-read-private playlist-modify-private playlist-modify-public'

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors"""
    pass

@lru_cache(maxsize=1)
def get_spotify_token():
    """
    Generate a Spotify access token.
    Cached for 1 hour to avoid regenerating unnecessarily.
    """
    try:
        # Check cache first
        cached_token = cache.get('spotify_access_token')
        if cached_token:
            return cached_token

        # Get credentials
        client_id = settings.SPOTIFY_CLIENT_ID
        client_secret = settings.SPOTIFY_CLIENT_SECRET

        if not all([client_id, client_secret]):
            raise SpotifyAPIError("Missing Spotify API credentials")

        # Get new token
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        })
        auth_response.raise_for_status()
        token = auth_response.json()['access_token']
        
        # Cache the token for 1 hour (3600 seconds)
        cache.set('spotify_access_token', token, timeout=3600)
        return token

    except Exception as e:
        raise SpotifyAPIError(f"Failed to generate Spotify access token: {str(e)}")

class SpotifyAPI:
    """Class to handle Spotify API requests"""
    
    BASE_URL = "https://api.spotify.com/v1"
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise SpotifyAPIError("Missing Spotify credentials in settings")
        
        # Use client credentials flow for non-user-specific operations
        self.client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=self.client_credentials_manager)
    
    @property
    def access_token(self):
        """Get the current access token from the client credentials manager"""
        return self.client_credentials_manager.get_access_token()['access_token']
    
    def search_track(self, track_name, artist_name):
        try:
            query = f"track:{track_name} artist:{artist_name}"
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                return results['tracks']['items'][0]['id']
            logger.warning(f"No track found for: {track_name} by {artist_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching track: {str(e)}")
            return None
            
    def create_playlist(self, name, description, track_ids):
        try:
            user_id = self.sp.current_user()['id']
            playlist = self.sp.user_playlist_create(
                user_id, 
                name,
                public=False,
                description=description
            )
            
            if track_ids:
                self.sp.playlist_add_items(playlist['id'], track_ids)
            return playlist['id']
            
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            raise

# Spotify API functions
def get_spotify_playlist(request, playlist_id):
    pass

def get_spotify_auth_url():
    params = {
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'scope': 'playlist-read-private playlist-modify-public playlist-modify-private',
        'show_dialog': True
    }
    return f'https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}'

def spotify_auth(request):
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

def spotify_callback(request):
    try:
        auth_code = request.GET.get('code')
        if not auth_code:
            raise Exception("No authorization code received")
            
        auth_manager = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="playlist-modify-public playlist-modify-private playlist-read-private"
        )
        
        token_info = auth_manager.get_access_token(auth_code)
        request.session['spotify_token'] = token_info['access_token']
        return redirect('convert_playlist')
            
    except Exception as e:
        logger.error(f"Error in spotify callback: {str(e)}")
        return redirect('error')

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

def search_tracks_on_spotify(track_info):
    spotify = SpotifyAPI()
    spotify_track_ids = []
    failed_tracks = []
    
    for track in track_info:
        track_id = spotify.search_track(track['name'], track['artist'])
        if track_id:
            spotify_track_ids.append(track_id)
        else:
            failed_tracks.append(f"{track['name']} by {track['artist']}")
            
    if failed_tracks:
        logger.warning(f"Failed to find tracks: {', '.join(failed_tracks)}")
        
    return spotify_track_ids
