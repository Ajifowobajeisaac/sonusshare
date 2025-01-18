# views.py

from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Song
from .tasks import convert_playlist_
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
import json
import redis
from .models import BetaTestingRequest
import logging
from .utils_spotify import get_spotify_auth_url, spotify_callback
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import util
import time
from .utils_apple_music import AppleMusicAPI
from .utils_spotify import search_tracks_on_spotify

logger = logging.getLogger(__name__)




def index(request):
    return render(request, 'sonoshareapp/index.html')

def get_access(request):
    return render(request, 'sonoshareapp/get_access.html')

def about(request):
    return render(request, 'sonoshareapp/about.html')

def contact(request):
    return render(request, 'sonoshareapp/contact.html')

def beta_testing(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Check if the email already exists in the database
        if BetaTestingRequest.objects.filter(email=email).exists():
            return render(request, 'sonoshareapp/beta_testing_exists.html', {'email': email})
        
        BetaTestingRequest.objects.create(email=email)
        
        # Send confirmation email to the user
        subject = 'Beta Testing Request Confirmation'
        message = 'Thank you for your interest in beta testing SonusShare! We have received your request and will review it shortly.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        try:
            send_mail(subject, message, from_email, recipient_list)
            logger.info(f"Confirmation email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending confirmation email to {email}: {str(e)}")
        
        # Send notification email to support@sonusshare.com
        subject = 'New Beta Testing Request'
        message = f'A new beta testing request has been submitted. Email: {email}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['support@sonusshare.com']
        try:
            send_mail(subject, message, from_email, recipient_list)
            logger.info(f"Notification email sent to support@sonusshare.com for {email}")
        except Exception as e:
            logger.error(f"Error sending notification email to support@sonusshare.com for {email}: {str(e)}")
        
        return render(request, 'sonoshareapp/beta_testing_success.html')
    
    return render(request, 'sonoshareapp/get_access.html')

def send_beta_testing_email(recipients=[]):
    subject = 'SonusShare Beta Testing Invitation'
    message = 'Dear user,\n\nWe are excited to invite you to participate in the beta testing of SonusShare! Your access has been granted, and you can now start using the application.\n\nTo get started, please visit our website at https://www.sonusshare.com and log in using your registered email address.\n\nWe appreciate your interest in testing SonusShare and helping us improve the platform. If you have any questions or feedback, please don\'t hesitate to reach out to us at support@sonusshare.com.\n\nBest regards,\nThe SonusShare Team'
    from_email = 'support@sonusshare.com'
    recipient_list = recipients
    
    sent_count = send_mail(subject, message, from_email, recipient_list)
    
    print(f"Email sent to {sent_count} recipient(s).")


def convert_playlist(request):
    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        destination = request.POST.get('destination')
        
        logger.info(f"Converting playlist to {destination}: {playlist_url}")
        
        # Start the Celery task
        task = convert_playlist_.delay(playlist_url, destination)
        request.session['task_id'] = task.id
        
        return JsonResponse({
            'task_id': task.id,
            'status': 'started'
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def progress(request):
    task_id = request.session.get('task_id')
    if task_id:
        return render(request, 'sonoshareapp/progress.html', {'task_id': task_id})
    else:
        return redirect('index')
    
def review_playlist(request):
    try:
        # Get data from session storage instead of GET parameters
        data = json.loads(sessionStorage.getItem('conversionData'))
        if not data:
            raise ValueError("No conversion data found")
            
        # Validate required fields
        required_fields = ['platform', 'playlist_name', 'track_ids', 'matched_tracks']
        if not all(field in data for field in required_fields):
            raise ValueError("Missing required conversion data")
            
        return render(request, 'sonoshareapp/review_playlist.html', data)
    except Exception as e:
        logger.error(f"Failed to render review page: {str(e)}")
        return redirect('error')

def error(request):
    error_message = request.GET.get('error_message', 'An unknown error occurred.')
    return render(request, 'sonoshareapp/error.html', {'error_message': error_message})

def test_redis_connection(request):
    redis_url = settings.CELERY_BROKER_URL
    try:
        redis_client = redis.from_url(redis_url, ssl_cert_reqs=None)
        redis_client.ping()
        return HttpResponse("Redis connection successful!")
    except redis.exceptions.ConnectionError as e:
        return HttpResponse(f"Redis connection failed: {str(e)}")

def spotify_auth(request):
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

def spotify_callback_view(request):
    try:
        code = request.GET.get('code')
        if not code:
            raise Exception("No authorization code received from Spotify")
            
        # Initialize Spotify OAuth
        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope='playlist-modify-public playlist-modify-private'
        )
        
        # Exchange code for token info
        token_info = sp_oauth.get_access_token(code)
        
        # Store both tokens in session
        request.session['spotify_token'] = token_info['access_token']
        request.session['spotify_refresh_token'] = token_info['refresh_token']
        request.session['token_expires_at'] = token_info['expires_at']
        
        # Check if there's a pending playlist creation
        if 'pending_playlist' in request.session:
            return redirect('create_spotify_playlist')
            
        return redirect('index')
        
    except Exception as e:
        error_message = f"Spotify authentication failed: {str(e)}"
        return redirect(f'/error/?error_message={error_message}')

def get_spotify_client(request):
    """Helper function to get a valid Spotify client with token refresh"""
    token = request.session.get('spotify_token')
    expires_at = request.session.get('token_expires_at')
    refresh_token = request.session.get('spotify_refresh_token')
    
    if not all([token, expires_at, refresh_token]):
        return None
        
    # Check if token needs refresh (if expires in less than 60 seconds)
    if int(time.time()) > expires_at - 60:
        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope='playlist-modify-public playlist-modify-private'
        )
        
        try:
            token_info = sp_oauth.refresh_access_token(refresh_token)
            request.session['spotify_token'] = token_info['access_token']
            request.session['token_expires_at'] = token_info['expires_at']
            if 'refresh_token' in token_info:
                request.session['spotify_refresh_token'] = token_info['refresh_token']
            token = token_info['access_token']
        except Exception:
            return None
            
    return spotipy.Spotify(auth=token)

def create_spotify_playlist(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        track_ids = request.POST.get('track_ids', '').split(',')
        
        logger.info(f"Attempting to create Spotify playlist: {name}")
        logger.debug(f"Track IDs: {track_ids}")
        
        sp = get_spotify_client(request)
        if not sp:
            logger.warning("No valid Spotify client - redirecting to auth")
            # Store pending playlist data
            request.session['pending_playlist'] = {
                'name': name,
                'description': description,
                'track_ids': track_ids
            }
            return redirect('spotify_auth')
            
        try:
            user_id = sp.me()['id']
            logger.info(f"Creating playlist for user: {user_id}")
            
            playlist = sp.user_playlist_create(user_id, name, description=description)
            sp.playlist_add_items(playlist['id'], track_ids)
            
            playlist_url = playlist['external_urls']['spotify']
            logger.info(f"Successfully created playlist: {playlist_url}")
            
            # Use the existing success template (referencing create_spotify_playlist.html lines 139-140)
            return render(request, 'sonoshareapp/create_spotify_playlist.html', {
                'playlist_url': playlist_url
            })
            
        except Exception as e:
            logger.error(f"Failed to create playlist: {str(e)}", exc_info=True)
            error_message = f"Failed to create Spotify playlist: {str(e)}"
            return redirect(f'/error/?error_message={error_message}')
    
    return redirect('index')

def create_spotify_playlist_helper(request, name, description, track_ids):
    client_id = settings.SPOTIFY_CLIENT_ID
    client_secret = settings.SPOTIFY_CLIENT_SECRET
    redirect_uri = settings.SPOTIFY_REDIRECT_URI
    scope = 'playlist-modify-public playlist-modify-private'

    try:
        # Try to get an existing token from the session
        token = request.session.get('spotify_token')
        if not token:
            # If no token exists, redirect to Spotify auth
            return redirect('spotify_auth')
            
        sp = spotipy.Spotify(auth=token)
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(user_id, name, description=description)
        sp.user_playlist_add_tracks(user_id, playlist['id'], track_ids)
        return playlist['external_urls']['spotify']
        
    except Exception as e:
        if 'token expired' in str(e).lower():
            # Clear the expired token and redirect to auth
            request.session.pop('spotify_token', None)
            return redirect('spotify_auth')
        raise e

def extract_playlist_id(url, platform):
    if platform == 'spotify':
        return url.split('/')[-1].split('?')[0]
    elif platform == 'apple_music':
        return url.split('/')[-1].split('?')[0]
    return None

def get_spotify_playlist(request, playlist_id):
    sp = get_spotify_client(request)
    if not sp:
        raise Exception("No valid Spotify client - please authenticate first")
    try:
        return sp.playlist(playlist_id)
    except Exception as e:
        logger.error(f"Failed to get Spotify playlist: {str(e)}")
        raise

def extract_track_info(tracks, platform):
    track_info = []
    
    if platform == 'spotify':
        for item in tracks:
            track = item['track']
            track_info.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'spotify_id': track['id']
            })
    elif platform == 'apple_music':
        for track in tracks:
            track_info.append({
                'name': track['attributes']['name'],
                'artist': track['attributes']['artistName'],
                'album': track['attributes']['albumName'],
                'duration_ms': track['attributes']['durationInMillis'],
                'apple_music_id': track['id']
            })
    return track_info

def search_track_on_apple_music(track_name, artist_name):
    try:
        apple_music = AppleMusicAPI()
        return apple_music.search_track(track_name, artist_name)
    except Exception as e:
        logger.error(f"Failed to search track on Apple Music: {str(e)}")
        return None
