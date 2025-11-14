from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .youtube_search import YouTubeSearcher
from django.http import HttpResponse
import os
import tempfile
import logging
import yt_dlp
import shutil

logger = logging.getLogger(__name__)

class YouTubeThumbnailView(APIView):
    """
    Proxy YouTube thumbnails through backend to avoid CORS issues
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        thumbnail_url = request.GET.get('url', '')
        if not thumbnail_url:
            return Response({'error': 'URL parameter required'}, status=400)

        try:
            import requests
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code == 200:
                return HttpResponse(response.content, content_type='image/jpeg')
            else:
                return Response({'error': 'Failed to fetch thumbnail'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class YouTubeSearchView(APIView):
    """
    API endpoint to search YouTube videos
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        query = request.GET.get('q', '')
        max_results = int(request.GET.get('max_results', 5))

        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)

        try:
            searcher = YouTubeSearcher()
            videos = searcher.search(query, max_results=max_results)
            return Response({'videos': videos})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class YouTubeDownloadView(APIView):
    """
    Download YouTube audio as MP3 using yt-dlp
    File is temporarily downloaded, served to frontend, then immediately deleted
    Supports both GET and POST methods
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        """Handle GET requests with ?url= parameter"""
        youtube_url = request.GET.get('url')
        return self._download_audio(youtube_url)

    def post(self, request, format=None):
        """Handle POST requests with url in body"""
        youtube_url = request.data.get('url')
        return self._download_audio(youtube_url)

    def _download_audio(self, youtube_url):
        """
        Core download logic using yt-dlp
        Downloads to temp directory, serves file, then cleans up immediately
        """
        if not youtube_url:
            return Response({'error': 'URL required'}, status=400)

        temp_dir = None
        try:
            logger.info(f"🔗 Starting download: {youtube_url}")

            # Create temp directory for this download
            temp_dir = tempfile.mkdtemp(prefix='youtube_dl_')
            output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

            # yt-dlp options - download best audio and convert to MP3
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            # Download video and extract metadata
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("📝 Extracting video info...")
                info = ydl.extract_info(youtube_url, download=True)
                song_name = info.get('title', 'audio')

                logger.info(f"📝 Title: {song_name}")

            # Find the downloaded MP3 file in temp directory
            downloaded_file = None
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    downloaded_file = os.path.join(temp_dir, file)
                    break

            if not downloaded_file or not os.path.exists(downloaded_file):
                raise Exception("Download completed but MP3 file not found")

            file_size = os.path.getsize(downloaded_file)
            logger.info(f"✓ Downloaded: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")

            if file_size == 0:
                raise Exception("Downloaded file is empty")

            # Read entire file into memory so we can delete it immediately
            with open(downloaded_file, 'rb') as audio_file:
                audio_data = audio_file.read()

            logger.info(f"✓ File read into memory: {len(audio_data)} bytes")

            # Clean up temp files BEFORE sending response
            # This is safe because we have the data in memory
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"🗑️ Cleaned up temp directory: {temp_dir}")
                temp_dir = None  # Mark as cleaned
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup error: {cleanup_error}")

            # Create HTTP response with the audio data
            response = HttpResponse(
                audio_data,
                content_type='audio/mpeg'
            )

            # Set headers for download
            safe_filename = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_'))[:50]
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}.mp3"'
            response['Content-Length'] = len(audio_data)
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache'

            logger.info(f"✓ Response ready: {len(audio_data)} bytes ({len(audio_data) / 1024 / 1024:.2f} MB)")
            logger.info(f"✓ Temporary files already cleaned up")

            return response

        except Exception as e:
            logger.error(f"✗ Download error: {str(e)}", exc_info=True)
            return Response({
                'error': str(e),
                'url': youtube_url
            }, status=500)

        finally:
            # Final cleanup in case something went wrong before the normal cleanup
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"🗑️ Final cleanup of temp directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.error(f"Final cleanup error: {cleanup_error}")
