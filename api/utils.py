import yt_dlp
import os
import tempfile
import shutil

class Video2Audio:
    """
    YouTube to Audio converter with bot detection bypass
    """
    def __init__(self, video_url, cookies_file=None):
        self.video_url = video_url
        self.cookies_file = cookies_file

    def convert(self, output_dir=None):
        """
        Download audio from YouTube video

        Args:
            output_dir: Optional directory to save file. If None, uses temp directory.

        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'title': str,
                'size': int,
                'temp_dir': str
            }
        """
        temp_dir = None
        try:
            print(f"🔗 Processing: {self.video_url}")

            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                temp_dir = output_dir
                is_temp = False
            else:
                temp_dir = tempfile.mkdtemp(prefix='video2audio_')
                is_temp = True

            output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

            # Enhanced yt-dlp options to bypass bot detection
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
                # Better headers to mimic real browser
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Sec-Fetch-Mode': 'navigate',
                },
                # Use Android client as fallback
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'player_skip': ['webpage'],
                    }
                },
            }

            # Add cookies if provided
            if self.cookies_file and os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                print(f"🍪 Using cookies from: {self.cookies_file}")
            else:
                # Try to use browser cookies (Chrome by default)
                try:
                    ydl_opts['cookiesfrombrowser'] = ('chrome',)
                    print("🍪 Attempting to use Chrome cookies")
                except:
                    print("⚠️ No cookies available, proceeding without authentication")

            # Download and extract info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("📝 Extracting video info...")
                info = ydl.extract_info(self.video_url, download=True)

                song_name = info.get('title', 'Unknown')
                thumbnail_url = info.get('thumbnail')

                print(f"📝 Title: {song_name}")

            # Find the downloaded MP3 file
            mp3_path = None
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    mp3_path = os.path.join(temp_dir, file)
                    break

            if not mp3_path or not os.path.exists(mp3_path):
                raise Exception("MP3 file not found after download")

            file_size = os.path.getsize(mp3_path)
            print(f"✓ Downloaded: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")

            if file_size == 0:
                raise Exception("Downloaded MP3 file is empty")

            print(f"✓ Successfully downloaded: {song_name}")

            return {
                'success': True,
                'file_path': mp3_path,
                'title': song_name,
                'size': file_size,
                'thumbnail_url': thumbnail_url,
                'temp_dir': temp_dir if is_temp else None
            }

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()

            if temp_dir and os.path.exists(temp_dir) and not output_dir:
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🗑️ Cleaned up temp directory after error: {temp_dir}")
                except Exception as cleanup_error:
                    print(f"⚠️ Cleanup error: {cleanup_error}")

            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def cleanup(temp_dir):
        """Helper method to cleanup temporary directory"""
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"🗑️ Cleaned up: {temp_dir}")
                return True
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
                return False
        return False
