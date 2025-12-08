import shutil
import os
from typing import Generator
import random
from pathlib import Path


src_prnt_dir = 'training_data/'
dest_dir = Path('triage_training_data/')
photos_to_copy = 30
sub_dir = os.listdir(src_prnt_dir)

def gen_src_directories(src_parent: str, src_sub: list) -> Generator[str, None, None]:
    for sd in src_sub:
        yield os.path.join(src_parent, sd)



def gen_photo_path() -> Generator[str, None, None]:
    for src_dir in gen_src_directories(src_prnt_dir, sub_dir):
        contents = os.listdir(src_dir)
        photo_filenames = []
        for _ in range(photos_to_copy):
            photo_name = random.choice(contents)
            while (photo_name in photo_filenames):
                photo_name = random.choice(contents)
            photo_filenames += photo_name
            yield os.path.join(src_dir, photo_name)

def copy_photos():
    for i,src_path in enumerate(gen_photo_path()):
        photo_num = f"{i}"
        dest_filename = Path(f"{photo_num}.jpg")
        dest_path = Path.joinpath(dest_dir, dest_filename)
        shutil.copy(src_path, dest_path)

copy_photos()