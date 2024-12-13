import struct
from pymodbus.client import ModbusTcpClient
import time
import sys
import csv
from datetime import datetime

# Add function to read and write coils
def read_coil(client, address):
    result = client.read_coils(address, count=1)
    if result.isError():
        print(f"Error reading coil at address {address}")
        return None
    return result.bits[0]

def write_coil(client, address, value):
    result = client.write_coil(address, value)
    if result.isError():
        print(f"Error writing coil at address {address}")

# Convert two 16-bit registers to an integer
def registers_to_int(high, low):
    packed = struct.pack('>HH', high, low)  # Pack as 32-bit
    return struct.unpack('>I', packed)[0]  # Unpack as integer

# Convert two 16-bit registers to a float
def registers_to_float(high, low):
    packed = struct.pack('>HH', high, low)  # Pack high and low registers
    return struct.unpack('>f', packed)[0]  # Unpack as float

# Read data from Modbus server
def read_data_from_modbus_server(client, start_address, num_rows, num_floats_per_row):
    data = []
    address = start_address
    for _ in range(num_rows):
        # Step 1: Read and reconstruct date-time components
        components = []
        for _ in range(5):  # Month, Day, Year, Hour, Minute
            result = client.read_holding_registers(address, count=2)
            if result.isError():
                print(f"Error reading data at address {address}")
                break
            high, low = result.registers
            components.append(registers_to_int(high, low))
            address += 2

        # Step 2: Read and reconstruct float values
        floats = []
        for _ in range(num_floats_per_row):
            result = client.read_holding_registers(address, count=2)
            if result.isError():
                print(f"Error reading data at address {address}")
                break
            high, low = result.registers
            floats.append(registers_to_float(high, low))
            address += 2

        # Combine date-time and float data
        data.append((components, floats))
    return data

# Format date-time components into "month/day/year hour:minute"
def format_date_time(components):
    try:
        # Format as MM/DD/YYYY HH:MM
        date_time = datetime(components[2], components[0], components[1], components[3], components[4])
        return date_time.strftime('%m/%d/%Y %H:%M')
    except ValueError:
        return "Invalid Date"

# Append data to CSV file
def append_to_csv(data, output_file):
    with open(output_file, 'a', newline='') as csvfile:  # Open in append mode
        writer = csv.writer(csvfile)
        # Write rows
        for components, floats in data:
            date_time = format_date_time(components)
            if date_time == "Invalid Date":
                print(f"Skipping row with invalid date: {components}")
                continue  # Skip rows with invalid dates
            row = [date_time] + floats[:4]  # Ensure only 4 float columns are written
            writer.writerow(row)

# Main function for Client 2 with two coils
def client_2_read_data_with_two_coils(server_ip, server_port, start_address, num_rows, num_floats_per_row, output_file, coil_sync_address, coil_done_address):
    # Create Modbus client
    client = ModbusTcpClient(server_ip, port=server_port)
    write_coil(client, coil_sync_address, 0)
    write_coil(client, coil_done_address, 0)

    # Initialize the CSV file with a header
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["DateTime", "Value1", "Value2", "Value3", "Value4"])

    if client.connect():
        while True:  # Continuous loop
            coil_sync_status = read_coil(client, coil_sync_address)
            coil_done_status = read_coil(client, coil_done_address)

            if coil_sync_status is None or coil_done_status is None:
                break

            # Exit if the done coil is set and sync coil is 0
            if coil_done_status == 1 and coil_sync_status == 0:
                print("Done coil is 1. Reading final data and exiting.")
                remaining_rows_response = client.read_holding_registers(250, count=1)
                if remaining_rows_response.isError():
                    print("Error reading remaining rows value.")
                else:
                    remaining_rows = remaining_rows_response.registers[0]
                    print(f"Remaining rows: {remaining_rows}")
                    data = read_data_from_modbus_server(client, start_address, remaining_rows, num_floats_per_row)
                    append_to_csv(data, output_file)  # Append the final batch of data
                    print(output_file + " created.")
                break


            # Read data if the sync coil is 1
            if coil_sync_status == 1:
                print("Coil_sync is 1. Reading data...")
                data = read_data_from_modbus_server(client, start_address, num_rows, num_floats_per_row)
                append_to_csv(data, output_file)  # Append data to CSV
                write_coil(client, coil_sync_address, 0)  # Signal ready for new data
            else:
                print("Coil_sync is 0. Waiting...")
            time.sleep(1)  # Avoid busy looping
        client.close()
    else:
        print("Failed to connect to Modbus server.")


print('Start Modbus Client Read')

time.sleep(2)

if len(sys.argv) != 6:
    print("Usage: python3 client2.py <server ip> <server port> <num_rows> <num_columns_with_floats> <output_csv>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
num_rows = int(sys.argv[3])
num_columns_with_floats = int(sys.argv[4])
output_csv = sys.argv[5]

start_time = time.time() 
client_2_read_data_with_two_coils(server_ip, server_port, 0, num_rows, num_columns_with_floats, output_csv, 0, 1)
end_time = time.time() 
elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time:.4f} seconds")