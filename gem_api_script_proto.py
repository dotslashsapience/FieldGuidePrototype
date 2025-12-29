from google.colab import drive
import os
import shutil
import time
import json
import PIL.Image
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

# Mount Drive
drive.mount('/content/drive')

# Install SDK if missing
try:
    import google.genai
except ImportError:
    !pip install -q -U google-genai
    from google import genai

# --- Configuration ---
API_KEY = "PASTE YOUR API KEY"
STOP_AFTER = 5000 
MAX_WORKERS = 15 

# Paths
SOURCE_PATH = "/content/drive/MyDrive/triage_training_data/unsorted_aryan"
DEST_BASE = "/content/drive/MyDrive/USABILITY_SORTING_ARYAN"
USABLE_PATH = os.path.join(DEST_BASE, "usable_aryan")
UNUSABLE_PATH = os.path.join(DEST_BASE, "unusable_aryan")

# Setup Client
client = genai.Client(api_key=API_KEY)
MODEL_NAME = 'gemini-2.5-flash' 

# Classification Prompt
SYSTEM_PROMPT = """
ROLE: Botanical Data Assistant.
TASK: Filter images for a plant classifier. These are FIELD PHOTOS.

INSTRUCTIONS:
1. Identify the primary plant subject.
2. If the main subject is IN FOCUS, it is USABLE.

CRITERIA FOR "USABLE":
- Focus: The main leaf/flower/fruit is sharp enough to identify species.
- Background: Other plants in the background are ACCEPTABLE.
- Lighting: Shadows are ACCEPTABLE if features are visible.
- Composition: Overlapping leaves are ACCEPTABLE.

CRITERIA FOR "UNUSABLE":
- Garbage: Fully blurry (motion blur).
- Empty: No plant visible.
- Extreme Distance: Plant is too small to see texture.
- Darkness: Subject not visible due to low light.

OUTPUT JSON: {"subject_type": "str", "reasoning": "str", "usable": bool}
"""

def process_single_image(image_name):
    img_path = os.path.join(SOURCE_PATH, image_name)
    
    try:
        img = PIL.Image.open(img_path)
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[SYSTEM_PROMPT, img],
            config=types.GenerateContentConfig(
                response_mime_type='application/json' 
            )
        )
        
        # Parse response
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:-3]
        data = json.loads(text)
        
        # Sort file
        if data.get("usable", False):
            shutil.copy2(img_path, os.path.join(USABLE_PATH, image_name))
        else:
            shutil.copy2(img_path, os.path.join(UNUSABLE_PATH, image_name))
            
        return True

    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return "QUOTA"
        return f"Error: {e}"

def run_batch():
    if not os.path.exists(SOURCE_PATH):
        print(f"Error: Source folder not found: {SOURCE_PATH}")
        return
        
    os.makedirs(USABLE_PATH, exist_ok=True)
    os.makedirs(UNUSABLE_PATH, exist_ok=True)

    # Get file list
    try:
        all_files = os.listdir(SOURCE_PATH)
    except FileNotFoundError:
        print("Error: Invalid source path.")
        return

    images = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic'))]
    
    # Deduplication
    already_processed = set(os.listdir(USABLE_PATH)) | set(os.listdir(UNUSABLE_PATH))
    images_to_process = [img for img in images if img not in already_processed][:STOP_AFTER]

    print(f"Processing {len(images_to_process)} images with {MAX_WORKERS} threads...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_single_image, img): img for img in images_to_process}
        
        for future in tqdm(as_completed(futures), total=len(images_to_process)):
            result = future.result()
            
            if result == "QUOTA":
                print("Rate limit hit. Pausing for 5s...")
                time.sleep(5) 

    print("Batch processing complete.")

if __name__ == "__main__":
    run_batch()