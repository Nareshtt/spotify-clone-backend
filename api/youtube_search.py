import yt_dlp
import requests

class YouTubeSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search(self, query, max_results=10):
        """Search YouTube using yt-dlp - most reliable method"""
        try:
            print(f"Searching for: {query}")

            # yt-dlp search options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Don't download, just get metadata
                'force_generic_extractor': False,
            }

            # Search using yt-dlp
            search_query = f"ytsearch{max_results}:{query}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(search_query, download=False)

                if not search_results or 'entries' not in search_results:
                    print("No search results found")
                    return []

                videos = []
                for entry in search_results['entries']:
                    if not entry:
                        continue

                    try:
                        video_id = entry.get('id', '')
                        title = entry.get('title', 'Unknown Title')
                        channel = entry.get('channel', entry.get('uploader', 'Unknown Channel'))
                        duration = entry.get('duration', 0)
                        thumbnail = entry.get('thumbnail', '')

                        # If no thumbnail, construct default YouTube thumbnail URL
                        if not thumbnail and video_id:
                            thumbnail = f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'

                        video_data = {
                            'id': video_id,
                            'title': title,
                            'thumbnail': thumbnail,
                            'channelName': channel,
                            'duration': self._format_duration(duration),
                            'url': f'https://www.youtube.com/watch?v={video_id}'
                        }

                        videos.append(video_data)
                        print(f"Found: {title} by {channel}")
                        print(f"Thumbnail URL: {thumbnail}")

                    except Exception as e:
                        print(f"Error processing video entry: {str(e)}")
                        continue

                return videos

        except Exception as e:
            print(f"yt-dlp search error: {str(e)}")
            # Fallback to alternative method if yt-dlp fails
            return self._fallback_search(query, max_results)

    def _fallback_search(self, query, max_results=10):
        """
        Fallback method using yt-dlp with direct YouTube search URL
        This is more reliable than web scraping
        """
        try:
            print("Using fallback search method...")

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlist_items': f'1-{max_results}',
            }

            # Direct YouTube search URL
            search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    result = ydl.extract_info(search_url, download=False)

                    if result and 'entries' in result:
                        videos = []
                        for entry in result['entries'][:max_results]:
                            if not entry:
                                continue

                            video_id = entry.get('id', '')
                            if not video_id:
                                continue

                            videos.append({
                                'id': video_id,
                                'title': entry.get('title', 'Unknown Title'),
                                'thumbnail': entry.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'),
                                'channelName': entry.get('channel', entry.get('uploader', 'Unknown')),
                                'duration': self._format_duration(entry.get('duration', 0)),
                                'url': f'https://www.youtube.com/watch?v={video_id}'
                            })

                        return videos
                except:
                    pass

            # If all else fails, return empty list
            print("All search methods failed")
            return []

        except Exception as e:
            print(f"Fallback search error: {str(e)}")
            return []

    def _format_duration(self, seconds):
        """Convert seconds to MM:SS or HH:MM:SS format"""
        if not seconds or seconds == 0:
            return '0:00'

        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60

            if hours > 0:
                return f'{hours}:{minutes:02d}:{secs:02d}'
            else:
                return f'{minutes}:{secs:02d}'
        except:
            return '0:00'


# Example usage and testing
if __name__ == "__main__":
    searcher = YouTubeSearcher()

    # Test search
    results = searcher.search("John Michael Howell", max_results=5)

    print(f"\n✓ Found {len(results)} videos:")
    for i, video in enumerate(results, 1):
        print(f"\n{i}. {video['title']}")
        print(f"   Channel: {video['channelName']}")
        print(f"   Duration: {video['duration']}")
        print(f"   URL: {video['url']}")
