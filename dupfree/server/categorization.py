import os
import sys
import torch
import clip
from PIL import Image
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from io import BytesIO
import requests
import webbrowser

def authenticate_google_drive(access_token):
    creds = Credentials(token=access_token)
    return build('drive', 'v3', credentials=creds)

def download_image(service, file_id):
    request = service.files().get_media(fileId=file_id)
    data = request.execute()
    return Image.open(BytesIO(data))

def categorize_files_with_clip(service, folder_id):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    categories = ["Human", "Animal", "Flower", "Landscape", "Vehicle", "Food"]
    text_inputs = torch.cat([clip.tokenize(f"a photo of {c}") for c in categories]).to(device)

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])

    if not files:
        print("No files found in folder.")
        return

    for file in files:
        file_id = file['id']
        name = file['name']
        mime_type = file['mimeType']

        if not mime_type.startswith('image/'):
            print(f"Skipping non-image file: {name}")
            continue

        try:
            image = preprocess(download_image(service, file_id)).unsqueeze(0).to(device)
            with torch.no_grad():
                image_features = model.encode_image(image)
                text_features = model.encode_text(text_inputs)
                similarity = (image_features @ text_features.T).softmax(dim=-1)
                category_idx = similarity.argmax().item()

            predicted_category = categories[category_idx]
            print(f"🔹 Image: {name} → Predicted Category: {predicted_category}")

            # Check or create target folder
            folder_query = f"name='{predicted_category}' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            folder_search = service.files().list(q=folder_query, fields="files(id)").execute()
            folder_list = folder_search.get('files', [])

            if folder_list:
                target_folder_id = folder_list[0]['id']
            else:
                folder_metadata = {
                    'name': predicted_category,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [folder_id]
                }
                folder = service.files().create(body=folder_metadata, fields='id').execute()
                target_folder_id = folder.get('id')

            # Copy file to categorized folder
            copied_file = {
                'name': name,
                'parents': [target_folder_id]
            }
            service.files().copy(fileId=file_id, body=copied_file).execute()

        except Exception as e:
            print(f"❌ Error processing {name}: {e}")

    print("\n✅ Classification and copying completed!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python categorization.py <folder_id> <access_token>")
        sys.exit(1)

    folder_id = sys.argv[1]
    access_token = sys.argv[2]

    service = authenticate_google_drive(access_token)
    categorize_files_with_clip(service, folder_id)
