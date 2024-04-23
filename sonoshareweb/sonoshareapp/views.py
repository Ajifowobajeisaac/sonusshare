from django.http import JsonResponse
from django.shortcuts import render
from .models import Song
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def test_create_song(request):
    try:
        # Set up Spotify API
        client_id = 'a11e3bfb94954f4d94d150e090851e9c'
        client_secret = 'b396b5e7d6c940a4a4d219a5bdcf3f07'
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # Extract the track information from the playlist
        track_name = "Bohemian Rhapsody"
        artist_name = "Queen"

        # Search for the tracks on Spotify
        results = sp.search(q=f'track:{track_name} artist:{artist_name}', type='track', limit=1)
        track = results['tracks']['items'][0]

        # Extract relevant song information
        track_id = track['id']
        track_title = track['name']
        track_artist = track['artists'][0]['name']
        track_album = track['album']['name']
        track_duration = track['duration_ms']

        # Create a new Song object
        song = Song.objects.create(
            title=track_title,
            artist=track_artist,
            service_id=track_id,
            service_name='Spotify',
            duration_ms=track_duration,
            album_name=track_album
        )

        return render(request, 'sonoshareapp/test_create_song.html', {'song': song})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
