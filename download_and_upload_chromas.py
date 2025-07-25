import os
import json
import requests
from datetime import datetime
import subprocess

# إعدادات Google Drive API
CLIENT_ID = os.getenv("DRIVE_CLIENT_ID")
CLIENT_SECRET = os.getenv("DRIVE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("DRIVE_REFRESH_TOKEN")

# مجلد Google Drive الهدف
FOLDER_ID = "1-qmqWnTIxI7obvRuHpVoBZCu7of8fWIi"

# اسم سجل الفيديوهات
LOG_FILE = "log.txt"

# كلمات البحث في يوتيوب
QUERY = "تلاوة قرآنية خلفية سوداء"
MAX_RESULTS = 10
DOWNLOAD_COUNT = 3

# تحميل توكن الوصول باستخدام التوكن المنعش
def get_access_token():
    url = "https://oauth2.googleapis.com/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    r = requests.post(url, data=payload)
    return r.json().get("access_token")

# تحميل سجل الفيديوهات السابقة
def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f.readlines())
    return set()

# حفظ الفيديوهات الجديدة في السجل
def save_to_log(video_ids):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for vid in video_ids:
            f.write(f"{vid}\n")

# البحث عن فيديوهات YouTube عبر API
def search_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": QUERY,
        "type": "video",
        "maxResults": MAX_RESULTS,
        "key": api_key
    }
    r = requests.get(url, params=params)
    results = r.json()
    videos = []
    for item in results.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        videos.append((video_id, title))
    return videos

# تحميل فيديو عبر yt-dlp
def download_video(video_id):
    url = f"https://youtu.be/{video_id}"
    subprocess.run(["yt-dlp", "-f", "best", "-o", f"{video_id}.mp4", url])

# رفع فيديو إلى Google Drive
def upload_to_drive(filename, access_token):
    metadata = {
        "name": filename,
        "parents": [FOLDER_ID]
    }
    files = {
        'data': ('metadata', json.dumps(metadata), 'application/json'),
        'file': (filename, open(filename, 'rb'))
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", 
                      headers=headers, files=files)
    return r.status_code == 200

# ---------- التنفيذ ---------- #
if __name__ == "__main__":
    access_token = get_access_token()
    downloaded = 0
    log = load_log()
    found = search_youtube()
    to_log = []

    for video_id, title in found:
        if video_id in log:
            continue
        print(f"Downloading: {title}")
        download_video(video_id)
        filename = f"{video_id}.mp4"
        print(f"Uploading to Drive: {filename}")
        success = upload_to_drive(filename, access_token)
        if success:
            to_log.append(video_id)
            downloaded += 1
            os.remove(filename)
        else:
            print(f"❌ Failed to upload {filename}")
        if downloaded >= DOWNLOAD_COUNT:
            break

    save_to_log(to_log)
    print(f"✅ Finished downloading and uploading {downloaded} video(s).")
