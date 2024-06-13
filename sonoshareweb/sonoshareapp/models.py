from django.db import models

class Song(models.Model):
    song_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    service_id = models.CharField(max_length=100)  # Can be 
    service_name = models.CharField(max_length=50)
    isrc = models.CharField(max_length=50, null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    album_name = models.CharField(max_length=200, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} by {self.artist}"

class MatchStatus(models.Model):
    match_status_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50)

    def __str__(self):
        return self.status

class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    original_url = models.URLField()
    source_service = models.CharField(max_length=50)
    destination_service = models.CharField(max_length=50)

    def __str__(self):
        return f"Playlist ({self.source_service} to {self.destination_service})"

class PlaylistSong(models.Model):
    playlistsong_id = models.AutoField(primary_key=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    match_status = models.ForeignKey(MatchStatus, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.song} in {self.playlist}"
    
class BetaTestingRequest(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
