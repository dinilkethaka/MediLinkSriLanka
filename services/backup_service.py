import os
import shutil
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import timezone, timedelta
SL_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Path to database file
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'medilink.db')

# Name of the folder in Google Drive
DRIVE_FOLDER_NAME = "MediLink Backups"


def authenticate():
    if not os.path.exists('token.json'):
        print("token.json not found. Run authorize_google.py first.")
        return None

    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open('token.json', 'w') as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                return None
        else:
            print("Credentials invalid. Run authorize_google.py again.")
            return None

    return build('drive', 'v3', credentials=creds)


def get_or_create_folder(service):
    query = (
        f"name='{DRIVE_FOLDER_NAME}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )

    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()

    files = results.get('files', [])

    if files:
        return files[0]['id']

    # Create the folder
    folder = service.files().create(
        body={
            'name': DRIVE_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        },
        fields='id'
    ).execute()

    print(f"Created Google Drive folder: {DRIVE_FOLDER_NAME}")
    return folder.get('id')


def upload_backup(service, folder_id):

    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        return None
    timestamp = datetime.now(SL_TIMEZONE).strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"medilink_{timestamp}.db"
    temp_path = f"temp_backup_{timestamp}.db"

    # Copy DB first so upload doesn't interfere with live database
    shutil.copy2(DB_PATH, temp_path)

    try:
        media = MediaFileUpload(
            temp_path,
            mimetype='application/octet-stream',
            resumable=True
        )

        uploaded = service.files().create(
            body={
                'name': backup_filename,
                'parents': [folder_id]
            },
            media_body=media,
            fields='id, name, size, createdTime'
        ).execute()

        size_kb = round(int(uploaded.get('size', 0)) / 1024, 1)
        print(f"Backup uploaded: {backup_filename} ({size_kb} KB)")

        return {
            "filename": backup_filename,
            "file_id": uploaded.get('id'),
            "size_kb": size_kb,
            "timestamp": timestamp
        }

    except Exception as e:
        print(f"Upload failed: {e}")
        return None

    finally:
        #delete tempory file
        if os.path.exists(temp_path):
            import time
            time.sleep(1)
            try:
                os.remove(temp_path)
            except PermissionError:
                time.sleep(2)
                try:
                    os.remove(temp_path)
                except PermissionError:
                    print(f"Could not delete temp file {temp_path} — delete it manually")

def run_backup():
    print(f"Starting backup at {datetime.now(SL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}")


    service = authenticate()
    if not service:
        return {
            "success": False,
            "message": "Google Drive authentication failed. Run authorize_google.py first."
        }

    try:
        folder_id = get_or_create_folder(service)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to access Google Drive folder: {str(e)}"
        }

    result = upload_backup(service, folder_id)

    if result:
        return {
            "success": True,
            "message": "Backup successful",
            "filename": result["filename"],
            "size_kb": result["size_kb"],
            "timestamp": result["timestamp"],
            "drive_folder": DRIVE_FOLDER_NAME
        }
    else:
        return {
            "success": False,
            "message": "Upload to Google Drive failed. Check your internet connection."
        }