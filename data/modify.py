import os
import sys
import csv

# Allow passing input/output paths as arguments or use environment variables
input_path = os.environ.get('GOOGLEPLAY_INPUT_PATH') or (sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'googleplaystore.csv'))
output_path = os.environ.get('GOOGLEPLAY_OUTPUT_PATH') or (sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), 'googleplaystore_fixed.csv'))

try:
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.reader((line.strip().strip('"') for line in infile))
        writer = csv.writer(outfile)
        for row in reader:
            # Remove double quotes from each field
            clean_row = [field.replace('"', '') for field in row]
            writer.writerow(clean_row)
    print(f"Fixed CSV saved to: {output_path}")
except FileNotFoundError:
    print(f"Input file not found: {input_path}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)