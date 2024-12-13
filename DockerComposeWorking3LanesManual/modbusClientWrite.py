import csv
import struct
from pymodbus.client import ModbusTcpClient
import time
import sys

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

# Convert an integer to two 16-bit registers
def int_to_registers(value):
    packed = struct.pack('>I', value)  # Pack integer as big-endian 32-bit
    high, low = struct.unpack('>HH', packed)  # Split into two 16-bit integers
    return high, low

# Convert float to two 16-bit registers
def float_to_registers(value):
    packed = struct.pack('>f', value)  # Pack float as big-endian IEEE 754
    high, low = struct.unpack('>HH', packed)  # Split into two 16-bit integers
    return high, low

# Parse date and time into individual components
def parse_date_time(date_time):
    date, time = date_time.split()  # Split into date and time
    month, day, year = map(int, date.split('/'))  # Split date into components
    year += 2000
    hour, minute = map(int, time.split(':'))  # Split time into components
    return [month, day, year, hour, minute]

# Modified function to send data to Modbus server with empty row check
def send_data_to_modbus_server_with_empty_check(client, data, start_address, coil_done_address):
    address = start_address
    for row in data:
        # Check if the row is empty or contains only empty values
        if not any(row):  # If the row is entirely empty
            print("Empty row detected. Stopping the program.")
            write_coil(client, coil_done_address, 1)  # Signal all data has been written
            return False  # Indicate the process should stop

        try:
            # Step 1: Extract and write date-time
            date_time = row[0]  # Assuming date-time is the first cell in each row
            components = parse_date_time(date_time)
            for component in components:
                high, low = int_to_registers(component)
                client.write_registers(address, [high, low])
                address += 2  # Increment address by 2 for each 32-bit value

            # Step 2: Write the float values
            for value in row[1:]:
                try:
                    float_value = float(value)
                    high, low = float_to_registers(float_value)
                    client.write_registers(address, [high, low])
                    address += 2
                except ValueError:
                    continue  # Skip non-numeric values
        except IndexError:
            continue  # Skip rows with missing data
    return True  # Indicate the process should continue

# Main function for Client 1 with two coils and empty row check
def client_1_send_data_with_two_coils_and_empty_check(csv_file_path, server_ip, server_port, start_address, coil_sync_address, coil_done_address):
    # Read CSV data
    with open(csv_file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        data = list(reader)

    # Create Modbus client
    client = ModbusTcpClient(server_ip, port=server_port)

    if client.connect():
        total_rows = len(data)
        print(total_rows)
        remaining_rows = total_rows
        current_row = 0
        write_coil(client, coil_sync_address, 0)
        write_coil(client, coil_done_address, 0)

        while True:  # Continuous loop
            coil_sync_status = read_coil(client, coil_sync_address)
            coil_done_status = read_coil(client, coil_done_address)

            if coil_sync_status is None or coil_done_status is None:
                break

            # Write data if the sync coil is 0
            if coil_sync_status == 0:
                if remaining_rows > 60:
                    print(f"Coil_sync is 0. Writing rows {current_row} to {current_row + 60}...")
                    rows_to_write = data[current_row:current_row + 60]
                    should_continue = send_data_to_modbus_server_with_empty_check(
                        client, rows_to_write, start_address, coil_done_address
                    )
                    if not should_continue:  # Stop the process if an empty row is detected
                        break
                    write_coil(client, coil_sync_address, 1)  # Signal data ready for reading
                    current_row += 60
                    remaining_rows -= 60
                else:
                    print(f"Coil_sync is 0. Writing rows {current_row} to {current_row + remaining_rows}...")
                    rows_to_write = data[current_row:current_row + remaining_rows]
                    send_data_to_modbus_server_with_empty_check(client, rows_to_write, start_address, coil_done_address)
                    client.write_register(250, remaining_rows)
                    write_coil(client, coil_done_address, 1)  # Signal all data has been written
                    print("All rows written. Setting coil_done to 1.")
                    break
            else:
                print("Coil_sync is 1. Waiting...")
            time.sleep(1)  # Avoid busy looping
        client.close()
    else:
        print("Failed to connect to Modbus server.")

        
print('Start Modbus Client Write')

time.sleep(2)

if len(sys.argv) != 4:
    print("Usage: python3 client2.py <csv_file_path> <server ip> <server port>")
    sys.exit(1)

csv_file_path = sys.argv[1]
server_ip = sys.argv[2]
server_port = sys.argv[3]

client_1_send_data_with_two_coils_and_empty_check(csv_file_path, server_ip, server_port, 0, 0, 1)
