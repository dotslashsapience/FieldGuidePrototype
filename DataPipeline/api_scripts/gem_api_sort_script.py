from pathlib import Path
from typing import Any, Generator
import os
import json
from google import genai
from google.genai import types
import shutil

CLIENT = genai.Client()
data_src_dir = '/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/triage_training_data/unsorted'
usable_dest_dir = '/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/triage_training_data/usable_for_training'
unusable_dest_dir = '/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/triage_training_data/unusable_for_training'
manrev_dest_dir = '/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/triage_training_data/manual_review'
log_file_path = '/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/logs/gem_script_log.txt'
img_files = os.listdir(data_src_dir)
ERROR_COUNT = 0
DUP_COUNT = 0
PROMPT = """
ROLE: Machine Learning Research Assistant.
TASK: Determine if the attached photo is usable for the purpose of training a ConvNext-small image classifier to
correctly identify plant species. The model will be used to identify 4000 distinct species. You should only mark for manual review
if you are uncertain of whether it is usable. If manual review is marked true, mark usable as false.

OUTPUT JSON: {"usable": bool, "manual_review": bool, "filename": str}

Omit ```JSON``` markings used for markdown rendering. Output pure json.
"""

def logger(err_msg: Exception, img_fname: str):
    log_entry = f"ERROR_NUM {ERROR_COUNT}, Image: {img_fname}, Error_Message: {err_msg}\n"
    with open(log_file_path, "a") as log:
        log.write(log_entry)

def get_img_bytes(file_path) -> bytes:
    with open (file_path, "rb") as file_content:
        image_bytes = file_content.read()
        return image_bytes

def get_files(src_dir: str) ->Generator[tuple[bytes, str, str], Any, None]:
    for img_fname in img_files:
        img_path = os.path.join(src_dir, img_fname)
        img_bytes = get_img_bytes(img_path)
        yield img_bytes, img_fname, img_path

def gen_api_calls(src_dir: str) -> Generator[tuple[dict, str, str], Any, Any]:
    for img_bytes, img_fname, img_path in get_files(src_dir):
        print(f'Querying: {img_fname}')
        try:
            response = CLIENT.models.generate_content(
                model="gemini-3-flash-preview",
                contents = [
                    types.Part.from_bytes(
                        data=img_bytes,
                        mime_type='image/jpeg'
                    ),
                    PROMPT + "file_name: " + img_fname
                ]
            )
            result = json.loads(str(response.text))
            yield result,img_fname, img_path
        except Exception as error_msg:
            logger(error_msg, img_fname)
            ERROR_COUNT += 1
            if ERROR_COUNT > 5:
                break
            continue
        
def sort_photos(src_dir: str) -> None:
        for result, img_fname, img_path in gen_api_calls(src_dir):
            if result["usable"]:
                dest_dir = usable_dest_dir
            else:
                if result["manual_review"]:
                    dest_dir = manrev_dest_dir
                else:
                    dest_dir = unusable_dest_dir
            print(f'Moving{img_fname}')
            try:
                shutil.move(img_path, dest_dir)
            except:
                dest_dir += f"{img_fname}-1.jpg"
                shutil.move(img_path, dest_dir)
            print()

sort_photos(data_src_dir)
