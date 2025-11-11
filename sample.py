from pytubefix import YouTube
import os

url = input("enter the youtube url: ")
yt = YouTube(url)
video = yt.streams.filter(only_audio=True).first()
out_file = video.download(output_path=".")
base, ext = os.path.splitext(out_file)
new_file = base + '.mp3'
os.rename(out_file, new_file)
print(f"Downloaded: {new_file}")
