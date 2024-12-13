#!/bin/bash

# Infinite loop to keep running the block of commands
while true; do
    # Run all three client read instances in parallel
    python3 modbusClientRead.py 192.168.2.6 1024 60 4 data-part1-o.csv &
    python3 modbusClientRead.py 192.168.2.7 1025 60 4 data-part2-o.csv &
    python3 modbusClientRead.py 192.168.2.8 1026 60 4 data-part3-o.csv &

    # Wait for all background processes to finish
    wait

    # Combine CSV files
    python3 combineCSV.py data-part1-o.csv data-part2-o.csv data-part3-o.csv results.csv

    # Optional: Add a delay to prevent overwhelming the system (e.g., 5 seconds)
    sleep 5
done
