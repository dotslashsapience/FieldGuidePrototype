from openai import OpenAI
from pathlib import Path
from typing import Any, Generator
import os
import json



client = OpenAI()

PROMPT = """I am using this API to sort photos of plant specimens for the purpose of creating a small dataset to train a simple 
image classifier model to clean up a larger dataset. The photo should be considered usable for training only if there is a clear single
dominant plant specimen to be identified and the photo is a close up of a distinctive feature of the plant such as a leaf and stem structure or a bloom or fruit.
 Your task with this prompt is to take the images that I have passed you 
and to categorize them. Your catagory options are:\n\n
usable_for_training: the photo has a clear identifiable target that is sufficiently dominant enough in the frame
for image classification training a convnext-small model.\n
blurry: the photo is blurry, grainy or noisy and should not be used for training.\n
distant_or_full_tree: the photo is a distant photo of the specimen or is a full height photo of a tree and should not be used
for training\n
insufficient_detail_closeup: the photo is a closeup with a clear target but lacks sufficient detail e.g. a closeup of a stem
structure that does not offer enough distinctive features for classification and should not be used for training.\n
noisy_background_unclear_target: the photo has too many different objects and/or no clearly dominant target in the photo and it
should not be used for training.\n
out_of_scope: The dominant target in the photo is not a plant specimen.\n
trunk_or_bark_nondistinctive: the photo has a clear target but is a non-distinctive close up image of tree bark or an image of a
tree trunk that should not be used for training.\n
underexposed_overexposed: the photo is either underexposed or overexposed and should not be used for training.\n
manual_review: this classification is for edge-case images for which you are uncertain of how to classify. Threshold for
this classification should be 80 percent. below 80 percent certainty of classification and you classify the image here.\n
Response format:\n
Your response should be only a json-style array with the following precise format and no additional characters.
any deviation from this format will break the program used to generate these API calls. Only one value should be true.\n
'[  {"photo": "filename",
        "usable_for_training": boolean,
        "blurry": boolean,
        "distant_or_full_tree": boolean,
        "insufficient_detail_closeup": boolean,
        "noisy_background_unclear_target": boolean,
        "out_of_scope": boolean,
        "trunk_or_bark_nondistinctive": boolean,
        "underexposed_overexposed": boolean,
        "manual_review": boolean },
    { "photo": "filename",
        "usable_for_training": boolean,
        ...(follow previous format for each photo)},
    {...},
    ...  
]'"""

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
file_ids_dict = {}

def create_file(file_path) -> str:
    with open (file_path, "rb") as file_content:
        result = client.files.create(
            file=file_content,
            purpose="vision"
        )
        return result.id
    

def get_file_ids() -> Generator[str, Any, None]:
    file_prnt_path = "triage_training_data/unsorted"
    for file in photo_filenames:
        photo_path = os.path.join(file_prnt_path, file)
        file_id = create_file(photo_path)
        file_ids_dict.update({file_id : file})
        yield file_id

def gen_api_calls():
    content = [{
        "type": "input_text", 
        "text": PROMPT
        }]
    for i,image in enumerate(get_file_ids()):
        image_dict = dict(type= 'input_image', file_id = image , detail='low')
        content.append(image_dict)
    input_prompt = [{
        "role": "user",
        "content": content
        }]
    response = client.responses.create(
        model="chatgpt-4o-latest",
        input= repr(input_prompt),
    )
    #results = json.loads(response.output_text)
    #for photo_dict in results:
        #photo_id = photo_dict.get("photo")
        #photo_dict.update({"photo" : file_ids_dict.get(photo_id)})
    #print(json.dumps(results, indent=4))
    print(response.output_text)

gen_api_calls()
    
    