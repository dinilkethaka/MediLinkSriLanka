from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authorize():
    if os.path.exists('token.json'):
        print("token.json already exists.")
        print("Delete it first if you want to re-authorize.")
        return

    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as f:
        f.write(creds.to_json())

    print("Authorization successful!")
    print("token.json has been created.")
    print("You can now run python app.py")

if __name__ == "__main__":
    authorize()