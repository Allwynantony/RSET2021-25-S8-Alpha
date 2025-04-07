from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import tempfile
import shutil
import webbrowser

app = Flask(__name__)
CORS(app)



def authenticate_google_drive(access_token):
    """Verify the access token and create Google Drive service"""
    try:
        creds = Credentials(access_token)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None

@app.route('/save-token', methods=['POST'])
def save_token():
    data = request.json
    access_token = data.get('accessToken')

    if not access_token:
        return jsonify({'error': 'No access token provided'}), 400

    print(f"Received Google Token: {access_token}") 
    return jsonify({'message': 'Token received successfully'})

@app.route('/run_duplication', methods=['POST'])
def run_duplication():
    data = request.json
    access_token = data.get('accessToken')
    folder_name = data.get('folderName')

    if not access_token:
        return jsonify({'error': 'No access token provided'}), 400
    if not folder_name:
        return jsonify({'error': 'No folder name provided'}), 400

    try:
        # Authenticate using the access token
        service = authenticate_google_drive(access_token)
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])

        if not folders:
            return jsonify({'error': 'Folder not found'}), 404

        folder_id = folders[0]['id']

       
        subprocess.run(['python3', 'duplication.py', folder_id, access_token], check=True)

        
        folder_url = f'https://drive.google.com/drive/folders/{folder_id}'
        webbrowser.open(folder_url) 

        return jsonify({'success': True, 'folderId': folder_id, 'folderUrl': folder_url})

    except Exception as e:
        print(f"Error during duplication: {str(e)}")
        return jsonify({'error': 'Failed to identify duplicates', 'details': str(e)}), 500


@app.route('/list-folders', methods=['POST'])
def list_folders():
    data = request.json
    access_token = data.get('accessToken')
    folder_name = data.get('folderName')  # Get the folder name from request

    if not access_token:
        return jsonify({'error': 'No access token provided'}), 400

    if not folder_name:
        return jsonify({'error': 'No folder name provided'}), 400

    try:
        service = authenticate_google_drive(access_token)
        
        # Search for the folder by name
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])

        if not folders:
            return jsonify({'error': 'Folder not found'}), 404

        folder_id = folders[0]['id']  # Get the first matching folder
        return jsonify({'folderId': folder_id})

    except Exception as e:
        print(f"Error fetching folders: {str(e)}")
        return jsonify({'error': 'Failed to retrieve folder', 'details': str(e)}), 500
 
 

@app.route('/categorize', methods=['POST'])
def categorize():
    data = request.json
    access_token = data.get('accessToken')
    folder_name = data.get('folderName')

    if not access_token:
        return jsonify({'error': 'No access token provided'}), 400
    if not folder_name:
        return jsonify({'error': 'No folder name provided'}), 400

    try:
        # Authenticate using the access token
        service = authenticate_google_drive(access_token)
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])

        if not folders:
            return jsonify({'error': 'Folder not found'}), 404

        folder_id = folders[0]['id']

  
        subprocess.run(['python3', 'categorization.py', folder_id, access_token], check=True)

   
        folder_url = f'https://drive.google.com/drive/folders/{folder_id}'
        webbrowser.open(folder_url)  

        return jsonify({'success': True, 'folderId': folder_id, 'folderUrl': folder_url})

    except Exception as e:
        print(f"Error during categorization: {str(e)}")
        return jsonify({'error': 'Failed to categorize files', 'details': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)

