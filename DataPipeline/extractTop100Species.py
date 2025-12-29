import csv

input_file = "wa_plants_species_over_100obs.csv"
plants = []
output_file = 'top_100_wa_plants.csv'

def extract_top_100(file_name):
    with open(file_name, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        print(fields)
        for plant in csvreader:
            if int(plant[2]) > 2776:
                plants.append(plant)


def save_top_100(output_filename):
    with open(output_filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(plants)

def main():
    extract_top_100(input_file)
    save_top_100(output_file)

main()