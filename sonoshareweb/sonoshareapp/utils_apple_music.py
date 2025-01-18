# utils_apple_music.py
import requests
import jwt
import time
import os
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache
from pathlib import Path

class AppleMusicAPIError(Exception):
    """Custom exception for Apple Music API errors"""
    pass

@lru_cache(maxsize=1)
def get_developer_token():
    """Generate an Apple Music developer token"""
    try:
        # Check cache first
        cached_token = cache.get('apple_music_dev_token')
        if cached_token:
            return cached_token

        # Get credentials from settings with fallback values
        team_id = settings.APPLE_TEAM_ID
        key_id = settings.APPLE_KEY_ID

        # Load private key
        key_path = Path(__file__).parent / 'apple_auth_key.p8'
        if not key_path.exists():
            raise FileNotFoundError(f"Apple Music private key not found at {key_path}")
            
        with open(key_path, 'r') as key_file:
            private_key = key_file.read()

        # Generate token
        token = jwt.encode(
            {
                'iss': team_id,
                'iat': int(time.time()),
                'exp': int(time.time() + 15777000),
            },
            private_key,
            algorithm='ES256',
            headers={
                'kid': key_id,
                'typ': 'JWT'
            }
        )

        # Test the token with a different endpoint
        test_url = "https://api.music.apple.com/v1/catalog/us/songs/203709340"
        test_headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(test_url, headers=test_headers)
            print(f"Test response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Test response content: {response.text}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Token test failed: {str(e)}")
            raise

        # Cache the valid token
        cache.set('apple_music_dev_token', token, timeout=43200)  # 12 hours
        return token

    except Exception as e:
        raise AppleMusicAPIError(f"Token generation failed. Full error: {str(e)}")

class AppleMusicAPI:
    """Class to handle Apple Music API requests"""
    
    BASE_URL = "https://api.music.apple.com/v1"
    
    def __init__(self, user_token=None):
        self.developer_token = get_developer_token()
        self.user_token = user_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.developer_token}",
            "Content-Type": "application/json"
        })
        if user_token:
            self.session.headers.update({"Music-User-Token": user_token})

    def _make_request(self, method, endpoint, **kwargs):
        """Generic method to make API requests"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise AppleMusicAPIError(f"API request failed: {str(e)}")

    def get_playlist(self, playlist_id, storefront='gb'):
        """Get a playlist by ID"""
        try:
            return self._make_request('GET', f"catalog/{storefront}/playlists/{playlist_id}")
        except Exception as e:
            raise AppleMusicAPIError(f"Failed to get playlist: {str(e)}")

    def create_playlist(self, name, description, track_ids):
        """Create a new playlist"""
        if not self.user_token:
            raise AppleMusicAPIError("User token required to create playlists")
            
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
        return self._make_request('POST', 'me/library/playlists', json=data)

    def search_track(self, track_name, artist_name, storefront='us', limit=1):
        """Search for a track"""
        params = {
            'types': 'songs',
            'term': f"{track_name} {artist_name}",
            'limit': limit
        }
        response = self._make_request('GET', f"catalog/{storefront}/search", params=params)
        
        try:
            tracks = response['results']['songs']['data']
            return tracks[0]['id'] if tracks else None
        except (KeyError, IndexError):
            return None

def get_apple_music_playlist(playlist_id):
    """Wrapper function for backward compatibility"""
    try:
        api = AppleMusicAPI()
        return api.get_playlist(playlist_id)
    except Exception as e:
        raise AppleMusicAPIError(f"Failed to get Apple Music playlist: {str(e)}")

def clean_private_key(key_content):
    """Clean and format the private key content."""
    if not key_content:
        return None
        
    # Remove any whitespace and ensure proper line breaks
    key_lines = [line.strip() for line in key_content.split('\n') if line.strip()]
    
    # Ensure proper PEM format
    if not key_lines[0].startswith('-----BEGIN PRIVATE KEY-----'):
        key_lines.insert(0, '-----BEGIN PRIVATE KEY-----')
    if not key_lines[-1].endswith('-----END PRIVATE KEY-----'):
        key_lines.append('-----END PRIVATE KEY-----')
    
    # Join with proper newlines
    return '\n'.join(key_lines)
