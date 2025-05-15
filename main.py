import os
import random
import json
import tempfile

import functions_framework
from yt_dlp import YoutubeDL
from google.cloud import secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# List of user agents to rotate
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "Mozilla/5.0 (X11; Linux x86_64)..."
]

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get('PROJECT_ID')
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def download_video(url, output_path):
    print(f"Starting download_video for URL: {url}")
    # Let yt-dlp auto-select best streams
    ydl_opts = {
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        "user-agent": random.choice(user_agents),
        "ignoreerrors": True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                print(f"yt-dlp failed for URL: {url}")
                return None
            filename = ydl.prepare_filename(info)
        print(f"Finished download_video, file: {filename}")
        return filename
    except Exception as e:
        print(f"Error in download_video: {e}")
        return None

def upload_to_drive(filepath):
    print(f"Starting upload_to_drive for file: {filepath}")
    creds_json = get_secret("AirtableWebhook")
    creds = service_account.Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=creds)

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None

    folder_id = "1qlOn9B5IPlwcSwN_wUeYBru13p3UsPdc"
    metadata = {"name": os.path.basename(filepath), "parents": [folder_id]}
    media = MediaFileUpload(filepath, resumable=True)

    file = service.files().create(
        body=metadata, media_body=media, fields="id, webViewLink"
    ).execute()

    url = file.get("webViewLink")
    print(f"Finished upload_to_drive, Drive URL: {url}")
    return url

@functions_framework.http
def process_video(request):
    print("process_video triggered")
    if request.method != "POST":
        return "Send a POST with JSON", 400

    data = request.get_json(silent=True)
    if not data or "URL" not in data or "recordId" not in data:
        return 'JSON must contain "URL" and "recordId"', 400

    url = data["URL"]
    record_id = data["recordId"]
    drive_urls = []

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Temp dir: {temp_dir}")
            filename = download_video(url, temp_dir)
            if not filename:
                return "Failed to download video", 500

            files = os.listdir(temp_dir)
            print(f"Contents of temp_dir after download: {files}")

            for fname in files:
                path = os.path.join(temp_dir, fname)
                link = upload_to_drive(path)
                if link:
                    drive_urls.append(link)

            if not drive_urls:
                return "Failed to upload", 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Internal Server Error", 500

    print("process_video completed successfully")
    return {"drive_urls": drive_urls, "record_id": record_id}

if __name__ == "__main__":
    functions_framework.run(
        target="process_video",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
    )
