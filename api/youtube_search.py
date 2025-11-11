import requests
import re
import json
from pytubefix import YouTube, Search

class YouTubeSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search(self, query, max_results=10):
        """Search YouTube using pytubefix Search - more reliable"""
        try:
            print(f"Searching for: {query}")

            # Use pytubefix Search for better reliability
            search = Search(query)
            videos = []

            # Get first 5 results
            for i, video in enumerate(search.results[:max_results]):
                try:
                    # Use pytubefix YouTube object like in utils.py
                    yt = YouTube(video.watch_url)

                    # Get video data using same method as utils.py
                    # Use direct thumbnail URL since we'll proxy it in frontend
                    thumbnail_url = yt.thumbnail_url

                    video_data = {
                        'id': yt.video_id,
                        'title': yt.title,
                        'thumbnail': thumbnail_url,  # Direct URL, frontend will proxy
                        'channelName': yt.author,
                        'duration': self._format_duration(yt.length),
                        'url': yt.watch_url
                    }
                    videos.append(video_data)
                    print(f"Found: {yt.title} by {yt.author}")
                    print(f"Thumbnail URL: {yt.thumbnail_url}")
                except Exception as e:
                    print(f"Error processing video {i}: {str(e)}")
                    continue

            return videos

        except Exception as e:
            print(f"Search error: {str(e)}")
            # Fallback to web scraping if pytubefix fails
            return self._fallback_search(query, max_results)

    def _fallback_search(self, query, max_results=10):
        """Fallback web scraping method"""
        try:
            search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}&sp=CAMSAhAB"  # Sort by relevance
            response = self.session.get(search_url)
            response.raise_for_status()

            videos = self._simple_extract(response.text)
            return videos[:max_results]

        except Exception as e:
            print(f"Fallback search error: {str(e)}")
            return []

    def _simple_extract(self, html_content):
        """Improved regex-based extraction with better thumbnails"""
        videos = []
        try:
            # More specific patterns for better results
            video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})".*?"title":{"runs":\[{"text":"([^"]+)"}\].*?"ownerText":{"runs":\[{"text":"([^"]+)"}\]'
            matches = re.findall(video_pattern, html_content, re.DOTALL)

            seen_ids = set()
            for video_id, title, channel in matches[:10]:  # Get more to filter duplicates
                if video_id in seen_ids:
                    continue
                seen_ids.add(video_id)

                if len(videos) >= 5:
                    break

                # Use multiple thumbnail sizes for better reliability
                thumbnail_urls = [
                    f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
                    f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg',
                    f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
                    f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg'
                ]

                # Test which thumbnail works
                thumbnail_url = thumbnail_urls[0]  # Default to first
                for thumb_url in thumbnail_urls:
                    try:
                        thumb_response = self.session.head(thumb_url, timeout=3)
                        if thumb_response.status_code == 200:
                            thumbnail_url = thumb_url
                            break
                    except:
                        continue

                videos.append({
                    'id': video_id,
                    'title': title.replace('\\u0026', '&').replace('\\', ''),
                    'thumbnail': thumbnail_url,
                    'channelName': channel.replace('\\u0026', '&').replace('\\', ''),
                    'duration': '0:00',
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })

        except Exception as e:
            print(f"Simple extract error: {str(e)}")

        return videos

    def _format_duration(self, seconds):
        """Convert seconds to MM:SS format"""
        if not seconds:
            return '0:00'
        minutes = seconds // 60
        seconds = seconds % 60
        return f'{minutes}:{seconds:02d}'

