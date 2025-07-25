import os
import json
import requests
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import yt_dlp

# إعداد المتغيرات البيئية
FOLDER_ID = 'YOUR_CHROMAS_FOLDER_ID'  # ضع ID مجلد الكرومات في Google Drive
LOG_FILE = 'log.txt'

CLIENT_ID = os.environ.get('DRIVE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('DRIVE_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('DRIVE_REFRESH_TOKEN')

TOKEN_URI = "https://oauth2.googleapis.com/token"

def get_access_token():
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    res = requests.post(TOKEN_URI, data=payload)
    return res.json().get("access_token")

def get_drive_service():
    access_token = get_access_token()
    creds = Credentials(token=access_token)
    return build('drive', 'v3', credentials=creds)

def load_log():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_log(video_id):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{video_id}\n")

def search_chroma_videos(max_results=3):
    query = 'تلاوة قرآنية خلفية سوداء'
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'maxResults': max_results * 3,
        'type': 'video',
        'key': os.environ.get('YOUTUBE_API_KEY')
    }
    response = requests.get(url, params=params)
    return response.json().get('items', [])

def download_video(video_id):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{video_id}.mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    return f'{video_id}.mp4'

def upload_to_drive(service, filepath):
    file_metadata = {
        'name': os.path.basename(filepath),
        'parents': [FOLDER_ID]
    }
    media = MediaFileUpload(filepath, mimetype='video/mp4', resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def main():
    log = load_log()
    service = get_drive_service()

    videos = search_chroma_videos(max_results=3)
    downloaded = 0

    for item in videos:
        video_id = item['id']['videoId']
        if video_id in log:
            continue

        print(f"⬇️ Downloading {video_id}")
        try:
            filename = download_video(video_id)
            print(f"⬆️ Uploading {filename} to Drive")
            upload_to_drive(service, filename)
            save_log(video_id)
            os.remove(filename)
            downloaded += 1
        except Exception as e:
            print(f"❌ Error with {video_id}: {e}")

        if downloaded >= 3:
            break

if __name__ == "__main__":
    main()
