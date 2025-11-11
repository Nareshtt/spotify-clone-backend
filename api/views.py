from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .youtube_search import YouTubeSearcher
from django.http import HttpResponse, FileResponse
from pytubefix import YouTube
import os
import tempfile

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
    def post(self, request, format=None):
        youtube_url = request.data.get('url')
        if not youtube_url:
            return Response({'error': 'URL required'}, status=400)

        try:
            yt = YouTube(youtube_url)
            song_name = yt.title

            audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
            if not audio_stream:
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

            if not audio_stream:
                return Response({'error': 'No audio stream available'}, status=400)

            # Use /tmp directory for Vercel
            temp_path = f"/tmp/{song_name[:50]}.mp3"

            audio_path = audio_stream.download(filename=temp_path)

            if not audio_path.endswith('.mp3'):
                mp3_path = audio_path.replace('.mp4', '.mp3')
                os.rename(audio_path, mp3_path)
                audio_path = mp3_path

            response = FileResponse(
                open(audio_path, 'rb'),
                as_attachment=True,
                filename=f"{song_name[:50]}.mp3",
                content_type='audio/mpeg'
            )

            return response

        except Exception as e:
            return Response({'error': str(e)}, status=500)
