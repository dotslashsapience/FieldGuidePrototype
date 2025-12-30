import os
import csv
import pandas as pd
import requests
from typing import List, Dict

# ======================
# GLOBAL CONFIGURATION
# ======================
TARGET_GEOGRAPHIC_REGION_NAME = "Washington"
INATURALIST_PLACE_ID_FOR_WASHINGTON = 46  #
INATURALIST_TAXON_ID_FOR_ALL_PLANTS = 47126 #

# Pipeline Limits
TOTAL_TOP_SPECIES_TO_INCLUDE_IN_MODEL = 2000
MAXIMUM_IMAGES_TO_COLLECT_PER_SPECIES = 1500
MINIMUM_IMAGES_REQUIRED_PER_SPECIES = 200

# File Paths
PATH_TO_BURKE_HERBARIUM_MASTER_LIST = "pnw_flora_species_2nd_ed.csv"
PATH_TO_MASSIVE_GBIF_METADATA_FILE = "observations.csv" # The 10GB+ file
PATH_TO_FINAL_IMAGE_EXTRACTION_LIST = "production_image_extraction_list.csv"

def get_top_ranked_washington_species(target_count: int) -> List[str]:
    """
    Queries iNaturalist to find the most-photographed plants in WA.
    This ensures our 'Backcountry OS' focuses on what hikers actually see.
    """
    print(f"--- RANKING TOP {target_count} SPECIES IN {TARGET_GEOGRAPHIC_REGION_NAME} ---")

    #
    api_endpoint_url = "https://api.inaturalist.org/v1/observations/species_counts"
    api_query_parameters = {
        "place_id": INATURALIST_PLACE_ID_FOR_WASHINGTON,
        "taxon_id": INATURALIST_TAXON_ID_FOR_ALL_PLANTS,
        "per_page": 200 # Maximum allowed by iNaturalist per page
    }

    identified_target_species_ids = []
    page_to_request = 1

    while len(identified_target_species_ids) < target_count:
        api_query_parameters["page"] = page_to_request
        api_response = requests.get(api_endpoint_url, params=api_query_parameters)
        api_response.raise_for_status()

        page_results = api_response.json().get("results", [])
        if not page_results:
            break

        for entry in page_results:
            if len(identified_target_species_ids) >= target_count:
                break

            taxon_data = entry.get("taxon", {})
            # Only accept species-level identifications
            if taxon_data.get("rank") == "species":
                identified_target_species_ids.append(str(taxon_data.get("id")))

        page_to_request += 1

    print(f"Identified {len(identified_target_species_ids)} species for the production model.")
    return identified_target_species_ids

def sift_massive_metadata_for_urls(target_species_ids: List[str]):
    """
    Uses 'Chunking' to process the 10GB file without crashing the laptop.
    Extracts URLs for the Top 2000 species.
    """
    print(f"--- STARTING EXTRACTION FROM {PATH_TO_MASSIVE_GBIF_METADATA_FILE} ---")


    fast_lookup_species_set = set(target_species_ids) #Checking if an ID exists

    # Track how many URLs we have found so we don't exceed the 1000 limit
    current_image_counts_per_species = {species_id: 0 for species_id in target_species_ids}

    with open(PATH_TO_FINAL_IMAGE_EXTRACTION_LIST, 'w', newline='') as output_csv_file:
        csv_writer = csv.writer(output_csv_file)
        csv_writer.writerow(["taxon_id", "scientific_name", "image_url"])

        #
        file_chunk_iterator = pd.read_csv(
            PATH_TO_MASSIVE_GBIF_METADATA_FILE,
            chunksize=100000,
            usecols=["taxon_id", "scientific_name", "image_url", "quality_grade"]
        )

        for data_chunk in file_chunk_iterator:
            # Step 1: Only keep "Research Grade" (high quality) images
            high_quality_only = data_chunk[data_chunk['quality_grade'] == 'research']

            # Step 2: Match against our Top 2000 list
            matches = high_quality_only[high_quality_only['taxon_id'].astype(str).isin(fast_lookup_species_set)]

            for _, row in matches.iterrows():
                species_id = str(row['taxon_id'])

                # Step 3: Enforce the 1,000 images per species limit
                if current_image_counts_per_species[species_id] < MAXIMUM_IMAGES_TO_COLLECT_PER_SPECIES:
                    csv_writer.writerow([species_id, row['scientific_name'], row['image_url']])
                    current_image_counts_per_species[species_id] += 1

    print(f"SUCCESS: Extraction List saved to {PATH_TO_FINAL_IMAGE_EXTRACTION_LIST}")

def main():
    # 1. Get the Top 2000 list via API
    target_ids = get_top_ranked_washington_species(TOTAL_TOP_SPECIES_TO_INCLUDE_IN_MODEL)

    # 2. Extract their photo URLs from the 10GB file
    sift_massive_metadata_for_urls(target_ids)

if __name__ == "__main__":
    main()