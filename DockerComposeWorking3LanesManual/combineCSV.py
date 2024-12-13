import csv
import sys

def combine_csv_files(file1, file2, file3, output_file):
    # Open the output file once and keep it open throughout
    with open(output_file, 'w', newline='') as out:
        writer = csv.writer(out)

        # Process the first file
        with open(file1, 'r') as f1:
            reader1 = csv.reader(f1)
            
            # Write the header from the first file
            header = next(reader1)
            writer.writerow(header)
            
            # Write all rows from the first file
            for row in reader1:
                writer.writerow(row)
        
        # Process the second and third files
        for file in [file2, file3]:
            with open(file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header
                for row in reader:
                    writer.writerow(row)


if len(sys.argv) != 5:
    print("Usage: python3 client2.py <file1> <file2> <file3> <output_file>")
    sys.exit(1)

# File paths
file1 = sys.argv[1]
file2 = sys.argv[2]
file3 = sys.argv[3]

# Output file path
output_file = sys.argv[4]

# Combine the CSV files
combine_csv_files(file1, file2, file3, output_file)

print(f"Combined CSV saved as {output_file}")
