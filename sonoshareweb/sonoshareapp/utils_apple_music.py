# utils_apple_music.py
import requests

APPLE_MUSIC_TOKEN = 'eyJhbGciOiJFUzI1NiIsImtpZCI6IjI0N0NaMzJSQUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiI3MzJOMzhMN0FNIiwiaWF0IjoxNzE1NjY1NTI1LCJleHAiOjE3MzE0NDI1MjV9.mlMPZwvG6eSi4D9SmJW_EzHlsPQ9EkghnStWwX9NFnaZYGfVrCACXhGAlVlzoUocH23f_S7EAz5RlMfPlPXWKw'


# Apple Music API functions
def get_apple_music_playlist(playlist_id):
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
