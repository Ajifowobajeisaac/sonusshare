from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Song
from .tasks import convert_playlist_
import json




def index(request):
    return render(request, 'sonoshareapp/index.html')

def convert_playlist(request):

    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        task = convert_playlist_.delay(playlist_url)
        return JsonResponse({'task_id': task.task_id})
    else:
        return redirect('index')
    # if request.method == 'POST':
    #     playlist_url = request.POST.get('playlist_url')
        
    #     if 'spotify.com' in playlist_url:
    #         try:
    #             playlist_id = extract_playlist_id(playlist_url, 'spotify')
    #             playlist = get_spotify_playlist(request, playlist_id)
    #             track_info = extract_track_info(playlist['tracks']['items'], 'spotify')
                
    #             for track in track_info:
    #                 track['apple_music_id'] = search_track_on_apple_music(request, track['name'], track['artist'])
                
    #             return create_apple_music_playlist(
    #                 playlist['name'],
    #                 playlist['description'],
    #                 [track['apple_music_id'] for track in track_info if track['apple_music_id']]
    #             )
    #         except Exception as e:
    #             return JsonResponse({'error': str(e)}, status=500)
        
    #     elif 'music.apple.com' in playlist_url:
    #         try:
    #             print("Extracting playlist ID from Apple Music URL")
    #             playlist_id = extract_playlist_id(playlist_url, 'apple_music')
    #             print(f"Extracted playlist ID: {playlist_id}")

    #             print("Fetching Apple Music playlist")
    #             playlist = get_apple_music_playlist(request, playlist_id)
    #             print("Apple Music playlist fetched successfully")

    #             print("Extracting track info from Apple Music playlist")
    #             track_info = extract_track_info(playlist['data'][0]['relationships']['tracks']['data'], 'apple_music')
    #             print(f"Extracted track info: {track_info}")
                
    #             spotify_track_ids = []
    #             spotify_tracks = {}
    #             for track in track_info:
    #                 # print(f"Searching for track on Spotify: {track['name']} by {track['artist']}")
    #                 spotify_tracks.update({track['name'] : track['artist']})
    #                 spotify_id = search_track_on_spotify(track['name'], track['artist'])
    #                 if spotify_id:
    #                     # print(f"Track found on Spotify with ID: {spotify_id}")
    #                     spotify_track_ids.append(spotify_id)
    #                 else:
    #                     print(f"Track not found on Spotify: {track['name']} by {track['artist']}")

    #             playlist_description = playlist['data'][0]['attributes'].get('description', {}).get('standard', '')
                
    #             print("Creating Spotify playlist")
    #             return render(request, 'sonoshareapp/review_playlist.html', {
    #                 'playlist_name': playlist['data'][0]['attributes']['name'],
    #                 'playlist_description': playlist_description,
    #                 'track_id' : spotify_track_ids,
    #                 'tracks' : spotify_tracks,
    #             })
    #         except spotipy.SpotifyException as e:
    #             if e.http_status == 429:
    #                 error_message = "Spotify API rate limit exceeded. Please try again later."
    #                 return render(request, 'sonoshareapp/error.html', {'error_message': error_message})
    #             else:
    #                 print(f"Error occurred: {str(e)}")
    #                 return JsonResponse({'error': str(e)}, status=500)
    #         except AttributeError as e:
    #             print(f"AttributeError occurred: {str(e)}")
    #             return JsonResponse({'error': str(e)}, status=500)
    #         except Exception as e:
    #             print(f"Error occurred: {str(e)}")
    #             return JsonResponse({'error': str(e)}, status=500)
    #     else:
    #         print("Invalid playlist URL")
    #         return JsonResponse({'error': 'Invalid playlist URL'}, status=400)
    
    # else:
    #     print("Request method is not POST. Redirecting to index.")
    #     return redirect('index')

def progress(request):
    task_id = request.session.get('task_id')
    if task_id:
        return render(request, 'sonoshareapp/progress.html', {'task_id': task_id})
    else:
        return redirect('index')
    
def review_playlist(request):
    data = json.loads(request.GET.get('data', '{}'))
    return render(request, 'sonoshareapp/review_playlist.html', data)

def error(request):
    error_message = request.GET.get('error_message', 'An unknown error occurred.')
    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})
