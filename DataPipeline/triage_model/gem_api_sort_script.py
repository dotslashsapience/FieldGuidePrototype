from pathlib import Path
from typing import Any, Generator
import os
import json
from google import genai
from google.genai import types

CLIENT = genai.Client()
PROMPT = """
ROLE: Machine Learning Research Assistant.
TASK: Determine if the attached photo is usable for the purpose of training a ConvNext-small image classifier to
correctly identify plant species. The model will be used to identify 4000 distinct species. You should only mark for manual review
if you are uncertain of whether it is usable. If manual review is marked true, mark usable as false.

OUTPUT JSON: {"usable": bool, "manual_review": bool, "filename": str}

Omit ```JSON``` markings used for markdown rendering. Output pure json.
"""

def get_img_bytes(file_path) -> bytes:
    with open (file_path, "rb") as file_content