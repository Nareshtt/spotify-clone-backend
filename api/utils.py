from pytubefix import YouTube
import os
from django.core.files import File
from django.core.files.base import ContentFile
import requests
from io import BytesIO
from .models import Song

class Video2Audio:
    def __init__(self, video_url):
        self.video_url = video_url
        self.yt = YouTube(video_url)

    def convert(self):
        """Get song info, download audio/thumbnail, and save to Song model"""
        try:
            song_name = self.yt.title
            print(f"Processing: {song_name}")

            # Download audio
            audio_stream = self.yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
            if not audio_stream:
                audio_stream = self.yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not audio_stream:
                raise Exception("No audio stream available")

            os.makedirs("temp_downloads", exist_ok=True)
            audio_path = audio_stream.download(output_path="temp_downloads")
            mp3_path = os.path.splitext(audio_path)[0] + '.mp3'
            os.rename(audio_path, mp3_path)

            # Download thumbnail
            thumbnail_response = requests.get(self.yt.thumbnail_url, timeout=10)
            thumbnail_content = BytesIO(thumbnail_response.content) if thumbnail_response.status_code == 200 else None

            # Create and save Song
            song = Song(song_name=song_name)
            with open(mp3_path, 'rb') as f:
                song.song_location.save(f"{song_name[:50]}.mp3", File(f), save=False)
            if thumbnail_content:
                song.profile_picture.save(f"{song_name[:50]}_thumbnail.jpg", ContentFile(thumbnail_content.read()), save=False)
            song.save()

            # Cleanup
            os.remove(mp3_path)

            print(f"✓ Successfully saved: {song_name}")
            return {'success': True, 'song': song}

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
