import os
import json
from datetime import datetime
from config import CONFIGS

config = CONFIGS["baseline_claude"]

# Specify the raw directory and output file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
raw_directory = './Datasets/Raw/' + config["DIRECTORY_NAME"]
output_file = f'./Datasets/Converted/{config["DIRECTORY_NAME"]}_{timestamp}.json'


def combine_json_files(raw_directory, output_file):
    combined_data = []

    # Get a list of JSON files in the raw directory
    json_files = [file for file in os.listdir(raw_directory) if file.endswith('.json')]

    # Iterate over each JSON file
    for json_file in json_files:
        file_path = os.path.join(raw_directory, json_file)

        # Read the JSON file and append its contents to the combined data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            combined_data.append(data)

    # Write the combined data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print(f"Combined JSON files saved to {output_file}")


# Call the function to combine JSON files
combine_json_files(raw_directory, output_file)
