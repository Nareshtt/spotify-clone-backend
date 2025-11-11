from rest_framework import serializers

class YouTubeURLSerializer(serializers.Serializer):
    url = serializers.URLField(
        required=True,
        help_text="YouTube video URL (e.g., https://www.youtube.com/watch?v=...)",
        label="YouTube URL",
        style={'placeholder': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}
    )

    def validate_url(self, value):
        """Validate that it's a YouTube URL"""
        if 'youtube.com' not in value and 'youtu.be' not in value:
            raise serializers.ValidationError("Please provide a valid YouTube URL")
        return value
