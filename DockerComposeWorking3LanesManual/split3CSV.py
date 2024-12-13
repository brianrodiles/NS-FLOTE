import csv
import math
import os
import sys
from datetime import datetime

def format_date(date_str):
    try:
        original_format = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')  # Original format
        return original_format.strftime('%-m/%-d/%Y %H:%M')  # Desired format
    except ValueError:
        return date_str  # Return as is if parsing fails

def split_csv_custom(input_file):
    # Determine base name and extension for output files
    base_name, ext = os.path.splitext(os.path.basename(input_file))
    
    # Read the input file
    with open(input_file, 'r') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # Read the header row
        rows = list(reader)  # Read all remaining rows into a list

    total_rows = len(rows)
    num_files = 3  # Number of parts to split into
    rows_per_file = math.ceil(total_rows / num_files)

    # Identify the date column index (if needed)
    date_column_index = header.index('DateTime') if 'DateTime' in header else None

    # Split rows and write to output files
    start_index = 0
    for i in range(num_files):
        end_index = min(start_index + rows_per_file, total_rows)
        output_file = f"{base_name}-part{i+1}{ext}"  # Generate dynamic filename
        with open(output_file, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)  # Write the header to each output file
            
            # Reformat rows and write them
            for row in rows[start_index:end_index]:
                if date_column_index is not None:
                    row[date_column_index] = format_date(row[date_column_index])
                writer.writerow(row)
        
        start_index = end_index
        print(f"Created: {output_file}")

# Check if the CSV file name is provided as an argument
if len(sys.argv) != 2:
    print("Usage: python3 client2.py <csv_file_path>")
    sys.exit(1)

csv_file_path = sys.argv[1]

# Example usage
split_csv_custom(csv_file_path)
