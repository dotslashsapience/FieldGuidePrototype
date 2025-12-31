import os
import csv
import pandas as pd
from typing import List, Dict

#Rename file to scrape_img_urls.py

# =====================
# GLOBAL CONFIGURATION
# =====================
PATH_TO_FILTERED_SPECIES_LIST = "../wa_plants_species_over_100obs.csv" #TGT_SPCS_LIST
PATH_TO_OBSERVATIONS = "../../observations.csv/observations.csv" #OBS_METADATA
PATH_TO_PHOTOS = "../../photos.csv/photos.csv" #IMG_METADATA
PATH_TO_FINAL_EXTRACTION_LIST = "production_image_extraction_list.csv" #IMG_URLS_DEST
MAXIMUM_IMAGES_TO_COLLECT_PER_SPECIES = 1500 #MAX_IMGS

#Once you refactor this, the name of the function that ties it all together can be something like get_img_urls()
def run_production_sift():
    # --- STAGE 1: LOAD TARGETS ---
    print(f"--- STAGE 1: LOADING TARGET SPECIES ---") #ditch the f-string, those are only used for special fields
    species_df = pd.read_csv(PATH_TO_FILTERED_SPECIES_LIST)
    target_ids = set(species_df['taxon_id'].astype(str).tolist())
    taxon_to_name = dict(zip(species_df['taxon_id'].astype(str), species_df['scientific_name']))
    print(f"Targeting {len(target_ids)} species.")
    # --- STAGE 2: SIFT OBSERVATIONS ---
    # We map observation_uuid -> taxon_id
    valid_observation_uuids = {}
    print(f"--- STAGE 2: SIFTING OBSERVATIONS (24.5 GB) ---")

    obs_iterator = pd.read_csv(
        PATH_TO_OBSERVATIONS,
        sep='\t',
        chunksize=200000,
        usecols=['observation_uuid', 'taxon_id', 'quality_grade']
    )

    for chunk in obs_iterator:
        # Ensure taxon_id is treated as a string and stripped of whitespace
        # Handle potential NaNs by dropping them before the comparison
        chunk = chunk.dropna(subset=['taxon_id'])

        # Convert to string and remove .0 if it was treated as a float
        chunk['taxon_id_str'] = chunk['taxon_id'].astype(float).astype(int).astype(str)

        matches = chunk[
            (chunk['quality_grade'] == 'research') &
            (chunk['taxon_id_str'].isin(target_ids))
            ]

        for _, row in matches.iterrows():
            valid_observation_uuids[row['observation_uuid']] = row['taxon_id_str']

        print(f"Processed chunk... Total UUIDs found: {len(valid_observation_uuids)}", end='\r')

    # --- STAGE 3: MAPPING PHOTOS & GENERATING URLs ---
    print(f"\n--- STAGE 3: MAPPING PHOTOS (43.5 GB) ---")
    counts_per_species = {tid: 0 for tid in target_ids}

    photo_iterator = pd.read_csv(
        PATH_TO_PHOTOS,
        sep='\t',
        chunksize=200000,
        usecols=['observation_uuid', 'photo_id', 'extension']
    )

    with open(PATH_TO_FINAL_EXTRACTION_LIST, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['taxon_id', 'scientific_name', 'image_url'])

        for chunk in photo_iterator:
            # Check if this photo belongs to one of our filtered observations
            matches = chunk[chunk['observation_uuid'].isin(valid_observation_uuids.keys())]

            for _, row in matches.iterrows():
                tid = valid_observation_uuids[row['observation_uuid']]
                ext = str(row['extension']).lower()

                # Check species cap and file extension
                if ext in ['jpg', 'jpeg'] and counts_per_species[tid] < MAXIMUM_IMAGES_TO_COLLECT_PER_SPECIES:
                    # CONSTRUCT THE URL MANUALLY [URLs are NOT PROVIDED DIRECTLY!!!]
                    photo_id = str(row['photo_id'])
                    generated_url = f"https://inaturalist-open-data.s3.amazonaws.com/photos/{photo_id}/medium.{ext}"

                    writer.writerow([tid, taxon_to_name[tid], generated_url])
                    counts_per_species[tid] += 1

            print(f"Scanning photos... Final URLs found: {sum(counts_per_species.values())}", end='\r')

    print(f"\nSUCCESS: Shopping list saved to {PATH_TO_FINAL_EXTRACTION_LIST}")

if __name__ == "__main__":
    run_production_sift()