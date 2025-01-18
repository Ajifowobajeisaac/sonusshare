import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root directory to Python path
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.append(project_root)

# Load .env file before Django setup with override
env_path = Path(project_root) / '.env'
print(f"\nLoading .env from: {env_path}")
load_result = load_dotenv(env_path, override=True)
print(f"Load result: {load_result}")

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonoshareweb.settings')

import django
django.setup()

from sonoshareapp.utils_apple_music import AppleMusicAPI, get_developer_token
from sonoshareapp.utils_spotify import SpotifyAPI

def test_apple_music_credentials():
    print("\nTesting Apple Music Credentials...")
    try:
        # Test developer token generation
        token = get_developer_token()
        print("✓ Successfully generated Apple Music developer token")
        
        # Test API instance creation
        api = AppleMusicAPI()
        print("✓ Successfully created Apple Music API instance")
        
        # Test a simple API call
        response = api.get_playlist('pl.a7e15641f20542418b0fb4a6057d165a')  # Today's Hits playlist
        print("✓ Successfully made test API call")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_spotify_credentials():
    print("\nTesting Spotify Credentials...")
    try:
        # Test API instance creation
        api = SpotifyAPI()
        print("✓ Successfully created Spotify API instance")
        
        # Test token generation
        token = api.access_token
        print("✓ Successfully generated Spotify access token")
        
        # Test a simple search
        result = api.search_track("Bohemian Rhapsody", "Queen")
        print("✓ Successfully made test API call")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def debug_environment():
    print("\nDEBUG ENVIRONMENT:")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {(Path(project_root) / '.env').exists()}")
    print(f".env file content:")
    try:
        with open(Path(project_root) / '.env', 'r') as f:
            env_content = f.read()
            print(env_content)
            
            # Parse and set environment variables directly
            for line in env_content.splitlines():
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    
    except Exception as e:
        print(f"Error reading .env: {e}")
    
    print("\nEnvironment Variables after direct setting:")
    print(f"APPLE_TEAM_ID: {os.environ.get('APPLE_TEAM_ID')}")
    print(f"APPLE_KEY_ID: {os.environ.get('APPLE_KEY_ID')}")

def main():
    print("Testing API Credentials\n" + "="*20)
    
    # Debug environment first
    debug_environment()
    
    # Test Apple Music
    apple_success = test_apple_music_credentials()
    
    # Test Spotify
    spotify_success = test_spotify_credentials()
    
    # Print summary
    print("\nCredentials Test Summary")
    print("="*20)
    print(f"Apple Music: {'✓ PASSED' if apple_success else '✗ FAILED'}")
    print(f"Spotify: {'✓ PASSED' if spotify_success else '✗ FAILED'}")

if __name__ == "__main__":
    main() 
