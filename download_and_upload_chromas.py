import os
import requests
import json
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# إعداد الاعتمادات
DRIVE_CLIENT_ID = os.environ["DRIVE_CLIENT_ID"]
DRIVE_CLIENT_SECRET = os.environ["DRIVE_CLIENT_SECRET"]
DRIVE_REFRESH_TOKEN = os.environ["DRIVE_REFRESH_TOKEN"]
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]

TOKEN_URL = "https://oauth2.googleapis.com/token"

def get_access_token():
    response = requests.post(TOKEN_URL, data={
        'client_id': DRIVE_CLIENT_ID,
        'client_secret': DRIVE_CLIENT_SECRET,
        'refresh_token': DRIVE_REFRESH_TOKEN,
        'grant_type': 'DRIVE_refresh_token',
    })
    return response.json().get("access_token")

def load_log():
    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_log(video_id):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(video_id + "\n")

def search_chroma_videos():
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "تلاوة قرآن خلفية سوداء",
        "type": "video",
        "videoDuration": "short",
        "maxResults": 10,
        "key": "AIzaSyCSif50bWhXh09pVzI_fUwA_NrLjx2aM2Q"  # مفتاح مؤقت أو يمكنك استخدام access_token في الطلب يدويًا
    }
    res = requests.get(search_url, params=params).json()
    return [(item["id"]["videoId"], item["snippet"]["title"]) for item in res.get("items", [])]

def download_video(video_id, title):
    from pytube import YouTube
    yt = YouTube(f"https://youtube.com/watch?v={video_id}")
    stream = yt.streams.filter(file_extension='mp4').first()
    filename = f"{title[:40].strip().replace(' ', '_')}.mp4"
    stream.download(filename=filename)
    return filename

def upload_to_drive(file_path, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    metadata = {
        'name': os.path.basename(file_path),
        'parents': [DRIVE_FOLDER_ID]
    }
    files = {
        'data': ('metadata', json.dumps(metadata), 'application/json'),
        'file': open(file_path, "rb")
    }
    response = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers=headers,
        files=files
    )
    return response.status_code == 200

def main():
    access_token = get_access_token()
    log = load_log()
    videos = search_chroma_videos()
    uploaded = 0

    for video_id, title in videos:
        if video_id in log:
            continue
        try:
            file_path = download_video(video_id, title)
            success = upload_to_drive(file_path, access_token)
            if success:
                save_log(video_id)
                uploaded += 1
            os.remove(file_path)
        except Exception as e:
            print("خطأ:", e)
        if uploaded >= 3:
            break

if __name__ == "__main__":
    main()
