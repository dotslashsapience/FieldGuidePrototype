from openai import OpenAI
from pathlib import Path
from typing import Any, Generator
import os
import json
from google import genai
from google.genai import types


CLIENT = genai.CLIENT()
FILE_PRNT_PATH = "triage_training_data/unsorted"
PROMPT = """You are an assistant that classifies photos of plant specimens into one of several categories
for dataset curation. You MUST answer in strict JSON only, with no extra text. Accompanying this prompt is exactly one photo.
Evaluate the accompanying image as follows. I will know if you hallucinate or deviate.

Goal:
Decide if each photo is usable for training a plant species classifier. A photo is usable only if:
- there is a single dominant plant specimen to be identified, and
- the image is a close-up of a distinctive feature such as leaf, stem structure, bloom, or fruit.

You must assign exactly ONE of the following labels to each photo:

- usable_for_training: clear, identifiable target; single dominant specimen; close-up of distinctive features; good focus/exposure.
- blurry: image is blurry, noisy, or grainy; details are not sharp enough for training.
- distant_or_full_tree: specimen is too far away or full-height tree; not enough detail on leaves/structures.
- insufficient_detail_closeup: close-up with a clear target but not enough distinctive features (e.g., generic stem or texture that does not support reliable classification).
- noisy_background_unclear_target: multiple plants or objects; no clearly dominant specimen; target ambiguous.
- out_of_scope: dominant target is not a plant specimen.
- trunk_or_bark_nondistinctive: close-up of non-distinctive bark or trunk image that does not show helpful features.
- underexposed_overexposed: photo is too dark or too bright, killing important detail.
- manual_review: you are uncertain between categories or the image is an edge case.

For each photo, you must output:
- "photo": the exact filename I provide below
- "label": one of the labels above
- "confidence": a number from 0.0 to 1.0 (your subjective confidence)
- "reason": a short explanation (one sentence)

Output format:
Return a single JSON array (NO surrounding quotes), where each element has this form:

{
  "photo": "FILENAME",
  "label": "one_of_the_labels_above",
  "confidence": 0.0,
  "reason": "short explanation"
}

Example output structure (for two photos):

[
  {
    "photo": "IMG_0001.JPG",
    "label": "usable_for_training",
    "confidence": 0.92,
    "reason": "Single leaf in sharp focus with simple background."
  },
  {
    "photo": "IMG_0002.JPG",
    "label": "noisy_background_unclear_target",
    "confidence": 0.78,
    "reason": "Several overlapping plants with no clear dominant specimen."
  }
]

Remember:
- Use ONLY valid JSON.
- Use ONLY the labels defined above.
- Exactly ONE label per photo.
- No extra text outside the JSON.

"""

photo_filenames = ["43.jpg",#bark
                   "36.jpg",#full tree or unclear target
                   "61.jpg", #usable
                   "242.jpg", #distant
                   "591.jpg", #insufficient detail closeup
                   "2086.jpg", #unclear target
                   "48.jpg", #trunk
                   "3007.jpg", #out of scope
                   "3010.jpg", #underexposed
                   "3006.jpg", #out of scope
                   "3002.jpg" #underexposed or insufficient detail
                   ]

temp_list_for_test = [
    
]

def get_img_bytes(file_path) -> bytes:
    with open (file_path, "rb") as file_content:
        image_bytes = file_content.read()
        return image_bytes
    

def get_file_ids() -> Generator[tuple[bytes, str], Any, None]:
    for file in photo_filenames:
        photo_path = os.path.join(FILE_PRNT_PATH, file)
        file_bytes = get_img_bytes
        (photo_path)
        yield file_bytes,file

def gen_api_calls():
    all_results = []
    for image, filename in get_file_ids():
        response = CLIENT.models.generate_content(
            model="gemini-2.5-flash",
            contents = [
            types.Part.from_bytes(
                data=image,
                mime_type='image/jpeg'
            ),
            PROMPT + "file_name: " + filename
        ]
        )
        results = response.text
        print(results)
        #results[0].update({"photo" : filename})
        all_results.append(results)
    #print(json.dumps(all_results, indent=4))
    

gen_api_calls()
    
