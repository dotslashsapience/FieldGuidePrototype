#from openai import OpenAI
from pathlib import Path
from typing import Any, Generator
import os
import json
from google import genai
from google.genai import types


CLIENT = genai.Client()
FILE_PRNT_PATH = "/home/ctristan/Pictures/unsorted_photos/unusable"
PROMPT1 = """You are an assistant that classifies photos of plant specimens into one of several categories
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
PROMPT2 = """
ROLE: Botanical Data Assistant.
TASK: Filter images for a plant classifier. These are FIELD PHOTOS. The usable photos will be used to train a  ConvNext-small
image classifier model to identify species of plant.

INSTRUCTIONS:
1. Identify the primary plant subject.
2. If the main subject is IN FOCUS, it is USABLE.

CRITERIA FOR "USABLE":
- Focus: The main target is sharp enough to identify species.
- Background: Other plants in the background are ACCEPTABLE as long as there is a clear target.
- Lighting: Shadows are ACCEPTABLE if features are visible.
- Composition: Overlapping leaves are ACCEPTABLE.
- Sharpness: Mild Blur is ACCEPTABLE if features are visible.

CRITERIA FOR "UNUSABLE":
- Garbage: Fully blurry (motion blur).
- Empty: No plant visible.
- Extreme Distance: Plant is too small to see texture.
- Darkness: Subject not visible due to low light.

EDGE CASES:
-mark for manual review

OUTPUT JSON: {"usable": bool, "manual_review": bool, "filename": str}
"""
PROMPT3 = """
ROLE: Machine Learning Research Assistant.
TASK: Determine if the attached photo is usable for the purpose of training a ConvNext-small image classifier to
correctly identify plant species. The model will be used to identify 4000 distinct species. You should only mark for manual review
if you are uncertain of whether it is usable. If manual review is marked true, mark usable as false.

OUTPUT JSON: {"usable": bool, "manual_review": bool, "filename": str, "reason": str}

Omit ```JSON``` markings used for markdown rendering. Output pure json.
"""
photo_filenames = ["6.jpg",#bark
                   "8.jpg",#full tree or unclear target
                   "14.jpg", #usable
                   "16.jpg", #distant
                   "28.jpg", #insufficient detail closeup
                   "30.jpg", #unclear target
                   "33.jpg", #trunk
                   "36.jpg", #out of scope
                   "38.jpg", #underexposed
                   "53.jpg", #out of scope
                   "51.jpg" #underexposed or insufficient detail
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
        file_bytes = get_img_bytes(photo_path)
        yield file_bytes,file

def gen_api_calls():
    all_results = []
    for image, filename in get_file_ids():
        response = CLIENT.models.generate_content(
            model="gemini-3-flash-preview",
            contents = [
            types.Part.from_bytes(
                data=image,
                mime_type='image/jpeg'
            ),
            PROMPT3 + "file_name: " + filename
        ]
        )
        results = response.text
        print(results)
        print()
        #results[0].update({"photo" : filename})
        all_results.append(results)
    #print(json.dumps(all_results, indent=4))
    

gen_api_calls()
    
