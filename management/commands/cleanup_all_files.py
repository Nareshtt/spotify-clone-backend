from django.core.management.base import BaseCommand
from api.models import Song
from api.cleanup import FileCleanupService

class Command(BaseCommand):
    help = 'Cleanup all song files from backend storage'

    def handle(self, *args, **options):
        songs = Song.objects.all()
        cleaned_count = 0
        
        for song in songs:
            if song.song_location or song.profile_picture:
                success = FileCleanupService.cleanup_song_files(song.id)
                if success:
                    cleaned_count += 1
                    self.stdout.write(f"Cleaned: {song.song_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned {cleaned_count} songs')
        )