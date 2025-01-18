# tasks.py

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from .utils import extract_track_info, extract_playlist_id, sanitize_description
from .utils_apple_music import AppleMusicAPI, AppleMusicAPIError
from .utils_spotify import SpotifyAPI, SpotifyAPIError
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def convert_playlist_(self, playlist_url, destination_platform):
    """
    Celery task to convert playlists between platforms.
    Args:
        self: Celery task instance (automatically injected)
        playlist_url (str): The URL of the playlist to convert
        destination_platform (str): The target platform ('spotify' or 'apple_music')
    """
    progress_recorder = ProgressRecorder(self)
    logger.info(f"Starting playlist conversion from URL: {playlist_url} to {destination_platform}")
    
    try:
        # Validate URL format
        if 'music.apple.com' in playlist_url:
            if '/playlist/' not in playlist_url:
                raise ValueError("Invalid Apple Music URL. Please provide a playlist URL.")
            
        elif 'spotify.com' in playlist_url:
            if '/playlist/' not in playlist_url:
                raise ValueError("Invalid Spotify URL. Please provide a playlist URL.")
        
        # Apple Music to Spotify conversion
        if 'music.apple.com' in playlist_url and destination_platform == 'spotify':
            playlist_id = extract_playlist_id(playlist_url, 'apple_music')
            logger.info(f"Extracted Apple Music playlist ID: {playlist_id}")
            
            apple_music = AppleMusicAPI()
            playlist_data = apple_music.get_playlist(playlist_id)
            
            if not playlist_data or 'data' not in playlist_data:
                raise AppleMusicAPIError("Invalid playlist data received")
                
            track_info = extract_track_info(
                playlist_data['data'][0]['relationships']['tracks']['data'], 
                'apple_music'
            )
            logger.info(f"Extracted {len(track_info)} tracks from Apple Music playlist")

            spotify = SpotifyAPI()
            spotify_track_ids = []
            spotify_tracks = {}
            failed_tracks = []
            matched_tracks = []
            
            total_tracks = len(track_info)
            for i, track in enumerate(track_info):
                current_track = f"{track['name']} by {track['artist']}"
                progress_recorder.set_progress(
                    i + 1, 
                    total_tracks,
                    description=f"Processing: {current_track}"
                )
                
                spotify_id = spotify.search_track(track['name'], track['artist'])
                
                if spotify_id:
                    spotify_track_ids.append(spotify_id)
                    spotify_tracks[track['name']] = track['artist']
                    matched_tracks.append({
                        'name': track['name'],
                        'artist': track['artist'],
                        'matched': True
                    })
                else:
                    failed_tracks.append(current_track)
                    matched_tracks.append({
                        'name': track['name'],
                        'artist': track['artist'],
                        'matched': False
                    })

            playlist_description = playlist_data['data'][0]['attributes'].get('description', {}).get('standard', '')
            
            if len(failed_tracks) > len(track_info) * 0.5:
                raise ValueError(f"Too many tracks failed to match: {len(failed_tracks)} out of {len(track_info)}")

            logger.info(f"Conversion completed. Successfully matched {len(spotify_track_ids)} tracks. Failed to match {len(failed_tracks)} tracks.")

            return {
                'platform': 'spotify',
                'playlist_name': f"{playlist_data['data'][0]['attributes']['name']}-converted",
                'playlist_description': sanitize_description(playlist_description),
                'track_ids': spotify_track_ids,
                'tracks': spotify_tracks,
                'failed_tracks': failed_tracks,
                'matched_tracks': matched_tracks,
                'success_rate': f"{(len(spotify_track_ids)/total_tracks)*100:.1f}%"
            }

        # Spotify to Apple Music conversion
        elif 'spotify.com' in playlist_url and destination_platform == 'apple_music':
            playlist_id = extract_playlist_id(playlist_url, 'spotify')
            logger.info(f"Extracted Spotify playlist ID: {playlist_id}")
            
            spotify = SpotifyAPI()
            playlist_data = spotify.get_playlist(playlist_id)
            
            if not playlist_data or 'tracks' not in playlist_data:
                raise SpotifyAPIError("Invalid playlist data received")
                
            track_info = extract_track_info(
                playlist_data['tracks']['items'], 
                'spotify'
            )
            logger.info(f"Extracted {len(track_info)} tracks from Spotify playlist")

            apple_music = AppleMusicAPI()
            apple_music_track_ids = []
            apple_music_tracks = {}
            failed_tracks = []
            
            total_tracks = len(track_info)
            for i, track in enumerate(track_info):
                apple_music_tracks.update({track['name']: track['artist']})
                apple_id = apple_music.search_track(track['name'], track['artist'])
                
                if apple_id:
                    apple_music_track_ids.append(apple_id)
                else:
                    failed_tracks.append(f"{track['name']} by {track['artist']}")

                progress_recorder.set_progress(i + 1, total_tracks)

            return {
                'platform': 'apple_music',
                'playlist_name': f"{playlist_data['name']}-converted",
                'playlist_description': sanitize_description(playlist_data.get('description', '')),
                'track_ids': apple_music_track_ids,
                'tracks': apple_music_tracks,
                'failed_tracks': failed_tracks
            }
            
        else:
            raise ValueError(f"Invalid playlist URL or unsupported platform combination: {playlist_url} to {destination_platform}")
            
    except Exception as e:
        logger.error(f"Error in convert_playlist_: {str(e)}", exc_info=True)
        raise
