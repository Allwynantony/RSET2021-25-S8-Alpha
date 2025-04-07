import os
import shutil
import numpy as np
import cv2
import imagehash
from PIL import Image
import sys
import io
import webbrowser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Authentication
def authenticate_google_drive(token):
    creds = Credentials(token)
    return build('drive', 'v3', credentials=creds)

#Downloading the images
def download_images_from_drive(service, folder_id, download_path):
    if os.path.exists(download_path):
        shutil.rmtree(download_path)
    os.makedirs(download_path)

    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    for item in items:
        request = service.files().get_media(fileId=item['id'])
        file_path = os.path.join(download_path, item['name'])
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    return download_path

# List images tht is in folder
def list_images_from_folder(folder_path):
    return [os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif', '.heic'))]

# Load images and resize
def load_images_resized(image_files, target_size=(256, 256)):
    images = []
    for file_path in image_files:
        image = Image.open(file_path).convert('RGB')
        image = image.resize(target_size)
        images.append(np.array(image))
    return np.array(images)

#Preprocess & Signature 
def preprocess_image(image: np.ndarray, hash_size: int) -> np.ndarray:
    return cv2.resize(image, (hash_size, hash_size))

def calculate_signature(image_array: np.ndarray, hash_size: int) -> np.ndarray:
    image_array = np.nan_to_num(image_array, nan=0.0)
    image_array = (image_array * 255).astype(np.uint8)
    pil_image = Image.fromarray(image_array).convert("L").resize(
        (hash_size, hash_size), Image.LANCZOS)
    phash = imagehash.phash(pil_image, hash_size=hash_size)
    signature = phash.hash.flatten()
    pil_image.close()
    return signature

# Duplicate Detection 
def find_near_duplicates(images, threshold, hash_size, bands, processed_pairs):
    rows = int(hash_size ** 2 / bands)
    signatures = {}
    hash_buckets_list = [{} for _ in range(bands)]

    for idx, image in enumerate(images):
        preprocessed = preprocess_image(image, hash_size)
        signature = calculate_signature(preprocessed, hash_size)
        signatures[idx] = np.packbits(signature)

        for i in range(bands):
            band = signature[i * rows: (i + 1) * rows]
            band_bytes = band.tobytes()
            hash_buckets_list[i].setdefault(band_bytes, []).append(idx)

    candidate_pairs = {
        (a, b) for bucket in hash_buckets_list
        for group in bucket.values() if len(group) > 1
        for i, a in enumerate(group) for b in group[i + 1:]
    }

    near_duplicates = []
    for idx_a, idx_b in candidate_pairs:
        if (idx_a, idx_b) in processed_pairs or (idx_b, idx_a) in processed_pairs:
            continue
        a, b = np.unpackbits(signatures[idx_a]), np.unpackbits(signatures[idx_b])
        similarity = (hash_size**2 - np.count_nonzero(a != b)) / (hash_size**2)
        if similarity >= threshold:
            near_duplicates.append((idx_a, idx_b))
            processed_pairs.update({(idx_a, idx_b), (idx_b, idx_a)})

    return near_duplicates

# === SIFT Duplicate Check ===
def sift_similarity(img1, img2, threshold=0.3):
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY), None)
    kp2, des2 = sift.detectAndCompute(cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY), None)
    if des1 is None or des2 is None:
        return False
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]
    return len(good) / min(len(kp1), len(kp2)) >= threshold if kp1 and kp2 else False

# === Save Duplicate Pairs ===
def save_duplicate_pairs(duplicates, image_files, output_folder):
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    for i, (a, b) in enumerate(duplicates, 1):
        Image.open(image_files[a]).convert("RGB").save(os.path.join(output_folder, f"{i}_dup_1.jpg"))
        Image.open(image_files[b]).convert("RGB").save(os.path.join(output_folder, f"{i}_dup_2.jpg"))

# === Upload to Drive ===
def upload_duplicates_to_drive(service, local_folder, parent_folder_id):
    # Create subfolder in Drive
    file_metadata = {
        'name': 'duplicates',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    duplicate_folder = service.files().create(body=file_metadata, fields='id').execute()
    duplicate_folder_id = duplicate_folder.get('id')

    for file_name in os.listdir(local_folder):
        file_path = os.path.join(local_folder, file_name)
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        service.files().create(
            body={'name': file_name, 'parents': [duplicate_folder_id]},
            media_body=media,
            fields='id'
        ).execute()

    return duplicate_folder_id

# === Main ===
if __name__ == "__main__":
    folder_id = sys.argv[1]
    access_token = sys.argv[2]

    service = authenticate_google_drive(access_token)
    local_path = "/tmp/drive_images"
    download_images_from_drive(service, folder_id, local_path)

    image_files = list_images_from_folder(local_path)
    images = load_images_resized(image_files)

    threshold = 0.55
    sift_threshold = 0.3
    hash_size = 32
    bands = 75
    processed_pairs = set()

    duplicates = find_near_duplicates(images, threshold, hash_size, bands, processed_pairs)

    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            if (i, j) in processed_pairs or (j, i) in processed_pairs:
                continue
            if sift_similarity(images[i], images[j], sift_threshold):
                duplicates.append((i, j))
                processed_pairs.update({(i, j), (j, i)})

    output_folder = os.path.join(local_path, "duplicates")
    save_duplicate_pairs(duplicates, image_files, output_folder)

    if duplicates:
        dup_folder_id = upload_duplicates_to_drive(service, output_folder, folder_id)
        dup_url = f"https://drive.google.com/drive/folders/{dup_folder_id}"
        #webbrowser.open_new_tab(dup_url)
        print(f"Duplicate images uploaded to: {dup_url}")
    else:
        print("No duplicates found.")
