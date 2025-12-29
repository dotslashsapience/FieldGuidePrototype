import requests
import csv

PLACE_ID_WA = 46          # Washington
PLANT_TAXON_ID = 47126    # Plantae
PER_PAGE = 200            # max per page allowed
MIN_OBS = 100             # minimum observation threshold
OUTFILE = "wa_plants_species_over_100obs.csv"


def fetch_species_counts():
    """
    Fetch species-level plant taxa for WA from iNaturalist,
    filtered by:
      - rank == 'species'
      - observation count >= MIN_OBS
    Returns a list of dicts ready for CSV export.
    """
    species = []
    page = 1

    while True:
        url = "https://api.inaturalist.org/v1/observations/species_counts"
        params = {
            "place_id": PLACE_ID_WA,
            "taxon_id": PLANT_TAXON_ID,
            "page": page,
            "per_page": PER_PAGE
        }

        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            break

        for entry in results:
            taxon = entry.get("taxon", {}) or {}

            # Only keep species-level
            if taxon.get("rank") != "species":
                continue

            count = entry.get("count", 0)
            if count < MIN_OBS:
                continue

            taxon_id = taxon.get("id")
            sci_name = taxon.get("name")

            if not taxon_id or not sci_name:
                continue

            species.append({
                "taxon_id": taxon_id,
                "scientific_name": sci_name,
                "observation_count": count,
                "inat_url": f"https://www.inaturalist.org/taxa/{taxon_id}"
            })

        page += 1

    return species


def main():
    print("Fetching WA species-level plant taxa with ≥100 observations...")
    species = fetch_species_counts()
    print(f"Total species retrieved: {len(species)}")

    # Write CSV
    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["taxon_id", "scientific_name", "observation_count", "inat_url"]
        )
        writer.writeheader()
        for row in species:
            writer.writerow(row)

    print(f"Saved CSV to {OUTFILE}")


if __name__ == "__main__":
    main()
