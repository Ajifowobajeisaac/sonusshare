import jwt
import time
import requests

def generate_developer_token(team_id, key_id, private_key):
    headers = {
        "alg": "ES256",
        "kid": key_id
    }
    payload = {
        "iss": team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 15777000  # 6 months
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return token

def search_apple_music(query, storefront, developer_token):
    url = f"https://api.music.apple.com/v1/catalog/{storefront}/search"
    headers = {
        "Authorization": f"Bearer {developer_token}"
    }
    params = {
        "term": query,
        "limit": 25,
        "types": "songs"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def create_apple_music_playlist(name, description, track_ids, developer_token):
    url = "https://api.music.apple.com/v1/me/library/playlists"
    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": user_token
    }
    data = {
        "attributes": {
            "name": name,
            "description": description
        },
        "relationships": {
            "tracks": {
                "data": [{"id": track_id, "type": "songs"} for track_id in track_ids]
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
