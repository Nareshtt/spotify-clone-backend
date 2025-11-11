from django.urls import path
from .views import (
    YouTubeThumbnailView,
    YouTubeSearchView,
    YouTubeDownloadView
)

urlpatterns = [
    path('search/', YouTubeSearchView.as_view(), name='youtube-search'),
    path('download/', YouTubeDownloadView.as_view(), name='youtube-download'),
    path('thumbnail/', YouTubeThumbnailView.as_view(), name='youtube-thumbnail'),
]
