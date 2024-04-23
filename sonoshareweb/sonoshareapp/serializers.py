from rest_framework import serializers
from .models import Song, MatchStatus, Playlist, PlaylistSong

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'  # Include all fields from the Song model

class MatchStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchStatus
        fields = '__all__'

class PlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = '__all__' 

class PlaylistSongSerializer(serializers.ModelSerializer):
    song = SongSerializer()  # Nested serializer
    match_status = MatchStatusSerializer()  

    class Meta:
        model = PlaylistSong
        fields = '__all__' 
