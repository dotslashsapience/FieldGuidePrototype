#%%
#The library to make HTTP requests
import requests
#%% md
# ### Import requests
# The requests library is a python library for HTTP requests. Documentation for the requests module can be found [here](https://requests.readthedocs.io/en/latest/ "Requests Documentation").
#%%
BASE = "https://www.inaturalist.org/observations.json"

params = {
    "taxon_id": 47126,
    "per_page": 100,
    "quality_grade": "research",
    "has[]": "photos"
}

def get_observations(BASE, params: dict):
    try:
        r = requests.get(BASE, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print("request failed: ", e)
        return None
#%% md
# #### get_observations
# The `requests.get()` method is an HTTP `GET` request method that takes in a base URL a dict of params and a timeout. We use the `raise_for_status()` method to raise an error message if our HTTP status != 200 OK. Then we return the JSON.
#%%

def iter_observations(base_url, base_params: dict):
    page = 1
    while True:
        params = base_params | {"page" : page} #pipe merges dict, rh-precedence for duplicates
        data = get_observations(base_url, params)#iNaturalist returns an array of JSON Objects.
        if not data:
            break
        yield from data #yield returns 1 item at a time from a generator iterating over results.
        page += 1
#%%
import csv

input_file = "top_100_wa_plants.csv"
taxon_names_dict = {} #dict that will associate the taxon_id with the scientific name.
taxon_ids = [] #List to store just the taxon ids to make generating searches easy
training_photos_dict = {} #dict to store urls for training photos
test_photos_dict = {} #dict to store urls for test data

def get_taxon_ids(input_filename: str) -> list[list]:
    with open(input_filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            taxon_names_dict[row[0]] = row[1]
            taxon_ids.append(row[0])
#%%
def generate_searches(search_terms: list, base_params: dict, txn_nms_dict: dict):
    for term in search_terms:
        prms = base_params | {"taxon_id": int(term)}
        yield txn_nms_dict[term], prms

#%%

def get_photo_urls(base_url: str, terms: list, base_params: dict, txn_nms_dict: dict):
    for item in generate_searches(terms, base_params, txn_nms_dict):
        species = item[0]
        prms = item[1]
        training_photos_dict[species] = []
        test_photos_dict[species] = []
        for obs in iter_observations(base_url, prms):
            photo_jsons = obs["photos"] # returns an array of dicts of all the photo info.

            for photo in photo_jsons:
                if len(training_photos_dict[species]) < 1000:
                    training_photos_dict[species].append(photo["large_url"])
                elif len(test_photos_dict[species]) < 5:
                    test_photos_dict[species].append(photo["large_url"])
                else: break
            if len(test_photos_dict[species]) >= 5: break
        if len(test_photos_dict[species]) < 5:
            needed_photos = 5 - len(test_photos_dict[species])
            test_photos_dict[species].append(training_photos_dict[species][-needed_photos:])

#%%
from fastcore.all import parallel
from fastdownload import download_url
from pathlib import Path
from typing import List, Tuple, Any

trng_path: Path = Path("training_data")
test_path: Path = Path("test_data")
DownloadArg = Tuple[str, Path]

def download_wrapper(url_and_path: DownloadArg):
    url, path = url_and_path
    try:
        download_url(url, path, timeout=10)
    except Exception as e:
        print(f"Failed to download: {url} to {path}")
#%%
def process_label_group(label: str, urls: list[str], root_path: Path) -> list[Any]:
    label_path: Path = root_path / label
    download_args: List[DownloadArg] = []
    for i, url in enumerate(urls):
        url_path = Path(url)
        filename: str = f"{i}{url_path.suffix or '.jpg'}"
        dest_path: Path = label_path / filename
        download_args.append((url, dest_path))
    print(f"Starting downloads for **{label}** ({len(urls)} items)")
    results: List[Any] = parallel(download_wrapper, download_args)
    return results
#%%
def download_images(training_dict: dict, test_dict: dict, trng_root_path: Path, test_root_path: Path):
    trng_root_path.mkdir(exist_ok=True)
    test_root_path.mkdir(exist_ok=True)
    trng_results: List[Any] = []
    test_results: List[Any] = []
    for label, urls in training_dict.items():
        results = process_label_group(label, urls, trng_root_path)
        trng_results.extend(results)
    print("\n\nTraining Photos downloaded, continuing to test photos.\n\n")
    for label, urls in test_dict.items():
        results = process_label_group(label, urls, test_root_path)
        test_results.extend(results)


#%%
def main():
    get_taxon_ids(input_file)
    get_photo_urls(BASE, taxon_ids, params, taxon_names_dict)
    download_images(training_photos_dict, test_photos_dict, trng_path, test_path)
#%%
main()
#%% md
# ## Parsing
# iNaturalist API returns a JSON object, it seems that there is no way to perfectly select particular species so we will need to scrape for research Grade photos which should indicate good quality and a positive ID, then we will need a separate function to filter for the observations that we want to use. From there we will need to get all of the photo urls from each observation and store them with the appropriate label and package them so that we can use the fastAI untar and download tool.
#%% md
# ### Getting a list of species
# iNaturalist has a get method we can use to get species counts. The species count can help us get a list of species for which there are observations.