from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .youtube_search import YouTubeSearcher
from django.http import HttpResponse
from django.conf import settings
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
    Download YouTube audio as MP3 using yt-dlp with bot detection bypass
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

    def _get_cookie_file_path(self):
        """
        Find the cookie file in multiple possible locations
        Priority: env var > project cookies dir > /tmp
        """
        # 1. Check environment variable
        env_path = os.environ.get('YOUTUBE_COOKIES_PATH')
        if env_path and os.path.exists(env_path):
            logger.info(f"🍪 Found cookies via env var: {env_path}")
            return env_path

        # 2. Check project cookies directory
        base_dir = getattr(settings, 'BASE_DIR', None)
        if base_dir:
            cookies_dir = os.path.join(base_dir, 'cookies', 'youtube.com_cookies.txt')
            if os.path.exists(cookies_dir):
                logger.info(f"🍪 Found cookies in project: {cookies_dir}")
                return cookies_dir

        # 3. Check current directory
        local_path = os.path.join(os.getcwd(), 'cookies', 'youtube.com_cookies.txt')
        if os.path.exists(local_path):
            logger.info(f"🍪 Found cookies in current dir: {local_path}")
            return local_path

        # 4. Check /tmp
        tmp_path = '/tmp/youtube_cookies.txt'
        if os.path.exists(tmp_path):
            logger.info(f"🍪 Found cookies in /tmp: {tmp_path}")
            return tmp_path

        logger.warning("⚠️ No cookie file found in any location")
        return None

    def _download_audio(self, youtube_url):
        """
        Core download logic using yt-dlp with enhanced bot detection bypass
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

            # Enhanced yt-dlp options - bypass bot detection
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                # Better headers to mimic a real browser
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Sec-Fetch-Mode': 'navigate',
                },
                # Use Android client as primary, web as fallback
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'player_skip': ['webpage'],
                    }
                },
            }

            # Try to find and load cookies
            cookie_file = self._get_cookie_file_path()

            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file
                logger.info(f"✓ Using cookie file: {cookie_file}")
            else:
                # Try browser cookies as fallback
                cookies_loaded = False
                for browser in ['chrome', 'firefox', 'edge', 'safari']:
                    try:
                        ydl_opts['cookiesfrombrowser'] = (browser,)
                        logger.info(f"🍪 Attempting to use {browser} cookies")
                        cookies_loaded = True
                        break
                    except Exception as e:
                        logger.debug(f"Could not load {browser} cookies: {e}")
                        continue

                if not cookies_loaded:
                    logger.error("❌ NO COOKIES AVAILABLE - Download will likely fail!")
                    logger.error("Please add youtube.com_cookies.txt to:")
                    logger.error("  1. /cookies/youtube.com_cookies.txt in project root")
                    logger.error("  2. Set YOUTUBE_COOKIES_PATH environment variable")
                    logger.error("  3. Place in /tmp/youtube_cookies.txt")

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
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"🗑️ Cleaned up temp directory: {temp_dir}")
                temp_dir = None
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup error: {cleanup_error}")

            # Create HTTP response with the audio data
            response = HttpResponse(audio_data, content_type='audio/mpeg')

            # Set headers for download
            safe_filename = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_'))[:50]
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}.mp3"'
            response['Content-Length'] = len(audio_data)
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache'

            logger.info(f"✓ Response ready: {len(audio_data)} bytes")
            return response

        except yt_dlp.utils.ExtractorError as e:
            error_msg = str(e)
            logger.error(f"✗ Extractor error: {error_msg}")

            # Provide helpful error message for bot detection
            if "Sign in to confirm" in error_msg or "not a bot" in error_msg:
                return Response({
                    'error': 'YouTube bot detection triggered',
                    'details': 'Cookie file is missing or expired. Please update youtube.com_cookies.txt',
                    'instructions': [
                        '1. Export fresh cookies from your browser using a cookie export extension',
                        '2. Save as cookies/youtube.com_cookies.txt in project root',
                        '3. Or set YOUTUBE_COOKIES_PATH environment variable',
                        '4. Restart the server'
                    ],
                    'url': youtube_url
                }, status=503)

            return Response({'error': error_msg, 'url': youtube_url}, status=500)

        except Exception as e:
            logger.error(f"✗ Download error: {str(e)}", exc_info=True)
            return Response({'error': str(e), 'url': youtube_url}, status=500)

        finally:
            # Final cleanup in case something went wrong
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"🗑️ Final cleanup of temp directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.error(f"Final cleanup error: {cleanup_error}")
