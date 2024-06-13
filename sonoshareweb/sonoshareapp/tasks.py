# tasks.py

from celery_progress.backend import ProgressRecorder
from .utils import extract_track_info, extract_playlist_id, sanitize_description
from .utils_apple_music import get_apple_music_playlist
from .utils_spotify import search_track_on_spotify
from celery import Celery, shared_task
import time



import os


app = Celery('tasks', broker=os.environ.get('STACKHERO_REDIS_URL_TLS'))
app.conf.update(
    result_backend=os.environ.get('STACKHERO_REDIS_URL_TLS'),
    task_serializer='json',
    result_serializer='json',
    accept_content=['application/json'],
    redis_backend_use_ssl={
        'ssl_cert_reqs': True
    }
)

@shared_task(bind=True)
def convert_playlist_(self, playlist_url):
    progress_recorder = ProgressRecorder(self)

    if 'music.apple.com' in playlist_url:
        try:
            playlist_id = extract_playlist_id(playlist_url, 'apple_music')
            playlist = get_apple_music_playlist(playlist_id)
            track_info = extract_track_info(playlist['data'][0]['relationships']['tracks']['data'], 'apple_music')

            spotify_track_ids = []
            spotify_tracks = {}
            total_tracks = len(track_info)

            for i, track in enumerate(track_info):
                spotify_tracks.update({track['name']: track['artist']})
                spotify_id = search_track_on_spotify(track['name'], track['artist'])
                if spotify_id:
                    spotify_track_ids.append(spotify_id)

                progress_recorder.set_progress(i + 1, total_tracks, description=f"Converting track {i + 1} of {total_tracks} ({track['name']} - {track['artist']})")

            playlist_description = playlist['data'][0]['attributes'].get('description', {}).get('standard', '')
            cleaned_description = sanitize_description(playlist_description)
            

            return {
                'playlist_name': f"{playlist['data'][0]['attributes']['name']}-converted",
                'playlist_description': cleaned_description,
                'track_id': spotify_track_ids,
                'tracks': spotify_tracks,
            }
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise
    else:
        raise ValueError("Invalid playlist URL")
