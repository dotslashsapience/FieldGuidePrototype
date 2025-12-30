import csv
import shutil
from typing import Generator, Any
from pathlib import Path
import os

input_file = "DataPipeline/triage_model/triage_audit.csv"
folders = []
subdirs = ['usable', 'unusable', 'manual_review']

def read_csv(filename) -> Generator[tuple[str, str, str, float], Any, None]:
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        for img in csvreader:
            img_fname = str(img[0])
            path = str(img[1])
            pred = str(img[2])
            energy = float(img[3])
            yield img_fname, path, pred, energy


def sort_photos():
    for img_fname, path, pred, energy in read_csv(input_file):
        root_path = Path(path).parent
        if root_path not in folders:
            folders.append(root_path)
            print(f"Now sorting: {root_path.name}")
        os.chdir(root_path)
        for folder in subdirs:
            (root_path / folder).mkdir(parents=True, exist_ok=True)
        if img_fname in os.listdir(root_path):
            if energy > -1.1938:
                shutil.move(img_fname, 'manual_review')
            elif pred == 'usable':
                shutil.move(img_fname, 'usable')
            elif pred == 'unusable':
                shutil.move(img_fname, 'unusable')
            
sort_photos()