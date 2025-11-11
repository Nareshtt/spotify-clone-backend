import yt_dlp
import os
import tempfile
import shutil

class Video2Audio:
    """
    Simple YouTube to Audio converter using yt-dlp
    Downloads temporarily, returns file path, caller is responsible for cleanup
    """
    def __init__(self, video_url):
        self.video_url = video_url

    def convert(self, output_dir=None):
        """
        Download audio from YouTube video

        Args:
            output_dir: Optional directory to save file. If None, uses temp directory.

        Returns:
            dict: {
                'success': bool,
                'file_path': str,  # Path to downloaded MP3
                'title': str,      # Video title
                'size': int,       # File size in bytes
                'temp_dir': str    # Temp directory path (for cleanup)
            }
        """
        temp_dir = None
        try:
            print(f"🔗 Processing: {self.video_url}")

            # Use provided output_dir or create temp directory
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                temp_dir = output_dir
                is_temp = False
            else:
                temp_dir = tempfile.mkdtemp(prefix='video2audio_')
                is_temp = True

            output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

            # yt-dlp options
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
            }

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

            # Cleanup on error if we created a temp directory
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
        """
        Helper method to cleanup temporary directory

        Args:
            temp_dir: Path to temporary directory to remove
        """
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"🗑️ Cleaned up: {temp_dir}")
                return True
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
                return False
        return False


# Example usage:
if __name__ == "__main__":
    # Example 1: Download to temp directory (auto-cleanup needed)
    converter = Video2Audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    result = converter.convert()

    if result['success']:
        print(f"✓ File saved at: {result['file_path']}")
        print(f"✓ Size: {result['size']} bytes")

        # Do something with the file...
        # ...

        # Clean up when done
        if result['temp_dir']:
            Video2Audio.cleanup(result['temp_dir'])
    else:
        print(f"✗ Error: {result['error']}")

    # Example 2: Download to specific directory (no cleanup needed)
    converter2 = Video2Audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    result2 = converter2.convert(output_dir="./downloads")

    if result2['success']:
        print(f"✓ File permanently saved at: {result2['file_path']}")
