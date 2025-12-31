import shutil
from typing import Generator, Any
from pathlib import Path
import os

TRNG_DAT_ROOT = Path('/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/training_data')
DEST_ROOT = Path('/home/ctristan/Documents/devlearning/PythonProjects/FieldGuidePrototype/triage_training_data/srtd_spcs_unusable')
SPECIES = os.listdir(TRNG_DAT_ROOT)
SUBDIRS = ['manual_review', 'unusable', 'usable']

def move_photos():
    SPECIES.sort()
    for spcs in SPECIES:
        print(f"Moving unusable photos for species: {spcs}")
        src_path = os.path.join(TRNG_DAT_ROOT, spcs)
        man_rev_path = os.path.join(src_path, SUBDIRS[0])
        unusable_path = os.path.join(src_path, SUBDIRS[1])
        usable_path = os.path.join(src_path, SUBDIRS[2])
        dest_path = os.path.join(DEST_ROOT, spcs)
        (DEST_ROOT / spcs).mkdir(parents=True, exist_ok=True)
        for img in os.listdir(man_rev_path):
            shutil.move(os.path.join(man_rev_path, img), dest_path)
        for img in os.listdir(unusable_path):
            shutil.move(os.path.join(unusable_path, img), dest_path)
        for img in os.listdir(usable_path):
            shutil.move(os.path.join(usable_path, img), src_path)
        os.rmdir(man_rev_path)
        os.rmdir(unusable_path)
        os.rmdir(usable_path)
            

           
           

move_photos()