# utils.py
import re
from html import unescape
from html.parser import HTMLParser


# Utility functions
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.plain_text = []

    def handle_data(self, data):
        self.plain_text.append(data)

    def get_plain_text(self):
        return ''.join(self.plain_text)

def sanitize_description(description):
    parser = MyHTMLParser()
    parser.feed(description)
    return parser.get_plain_text()


def extract_playlist_id(playlist_url, platform):
    if platform == 'spotify':
        pattern = re.compile(r'playlist/([a-zA-Z0-9_-]+)')
    elif platform == 'apple_music':
        pattern = re.compile(r'pl\.([a-zA-Z0-9_-]+)')
    else:
        return None

    match = pattern.search(playlist_url)
    if match:
        if platform == 'apple_music':
            return f"pl.{match.group(1)}"  # Include the 'pl.' prefix for Apple Music
        else:
            return match.group(1)
    else:
        return None

def extract_track_info(tracks, platform):
    track_info = []
    for track in tracks:
        if platform == 'spotify':
            track_info.append({
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name'],
                'spotify_id': track['track']['id'],
                'apple_music_id': None  # You'll need to search for the track on Apple Music and get its ID
            })
        elif platform == 'apple_music':
            track_info.append({
                'name': track['attributes']['name'],
                'artist': track['attributes']['artistName'],
                'apple_music_id': track['id'],
                'spotify_id': None  # You'll need to search for the track on Spotify and get its ID
            })
    return track_info
