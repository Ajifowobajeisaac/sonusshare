# utils.py
import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs


# Utility functions
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.plain_text = []

    def handle_data(self, data):
        self.plain_text.append(data)

    def get_plain_text(self):
        return ''.join(self.plain_text)

class PlaylistError(Exception):
    """Custom exception for playlist-related errors"""
    pass

def sanitize_description(description):
    """Clean and format playlist descriptions"""
    if not description:
        return ""
    
    # Remove HTML tags
    clean_desc = re.sub(r'<[^>]+>', '', description)
    
    # Remove excessive whitespace
    clean_desc = ' '.join(clean_desc.split())
    
    # Limit length
    MAX_LENGTH = 300
    if len(clean_desc) > MAX_LENGTH:
        clean_desc = clean_desc[:MAX_LENGTH-3] + '...'
    
    return clean_desc

def extract_playlist_id(url, service):
    """Extract playlist ID from various streaming service URLs"""
    try:
        parsed_url = urlparse(url)
        
        if service == 'spotify':
            # Handle Spotify URLs
            path_parts = parsed_url.path.split('/')
            if 'playlist' in path_parts:
                return path_parts[path_parts.index('playlist') + 1]
        
        elif service == 'apple_music':
            # Handle Apple Music URLs
            path_parts = parsed_url.path.split('/')
            if 'playlist' in path_parts:
                return path_parts[-1]
        
        elif service == 'youtube':
            # Handle YouTube URLs
            if 'list' in parse_qs(parsed_url.query):
                return parse_qs(parsed_url.query)['list'][0]
        
        raise PlaylistError(f"Could not extract playlist ID from {url}")
    
    except Exception as e:
        raise PlaylistError(f"Error extracting playlist ID: {str(e)}")

def extract_track_info(tracks_data, service):
    """Extract standardized track information from various services"""
    try:
        track_info = []
        
        for track in tracks_data:
            if service == 'spotify':
                info = {
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'isrc': track.get('external_ids', {}).get('isrc')
                }
            
            elif service == 'apple_music':
                info = {
                    'name': track['attributes']['name'],
                    'artist': track['attributes']['artistName'],
                    'album': track['attributes']['albumName'],
                    'duration_ms': track['attributes']['durationInMillis'],
                    'isrc': track['attributes'].get('isrc')
                }
            
            track_info.append(info)
        
        return track_info
    
    except Exception as e:
        raise PlaylistError(f"Error extracting track info: {str(e)}")
