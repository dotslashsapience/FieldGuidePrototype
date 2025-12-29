import requests
import zipfile
import io
import csv

CHECKLIST_URL = "https://burkeherbarium.org/pnwflora/data/PNWFloraChecklist.zip"
OUTFILE = "pnw_flora_species_2nd_ed.csv"


def download_checklist_zip():
    resp = requests.get(CHECKLIST_URL)
    resp.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(resp.content))



def extract_species(z: zipfile.ZipFile, taxa_filename: str):
    """
    Parse the 2nd edition table and extract accepted species-level taxa.
    Column names are based on the checklist docs; print them once and adjust if needed. :contentReference[oaicite:2]{index=2}
    """
    species = []

    with z.open(taxa_filename) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        print("Columns in 2nd edition table:", reader.fieldnames)

        for row in reader:
            # From the docs, typical fields include:
            #   NameRank, ScientificName, Accepted, Treated, TaxonName, Origin, etc.
            rank = (row.get("NameRank") or "").lower()
            accepted_flag = (row.get("Accepted") or "").upper()
            treated_flag = (row.get("Treated") or "").upper()
            sci_name = (row.get("TaxonName") or row.get("ScientificName") or "").strip()

            # Keep only accepted, treated species
            if rank != "species":
                continue
            if accepted_flag not in ("Y", "YES", "TRUE", "T"):
                continue
            if treated_flag not in ("Y", "YES", "TRUE", "T", ""):
                # you can tighten or loosen this depending on how strict you want to be
                continue
            if not sci_name:
                continue

            species.append({"scientific_name": sci_name})

    return species


def main():
    print("Downloading PNW Flora checklist ZIP...")
    z = download_checklist_zip()

    print("Locating 2nd edition taxa file...")
    taxa_file = "scientificnames.txt"
    print("Using:", taxa_file)

    print("Extracting accepted species-level taxa...")
    species = extract_species(z, taxa_file)
    print(f"Extracted {len(species)} species")

    print(f"Writing species list to {OUTFILE}...")
    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scientific_name"])
        writer.writeheader()
        writer.writerows(species)

    print("Done.")


if __name__ == "__main__":
    main()
