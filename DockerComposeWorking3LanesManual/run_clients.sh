#!/bin/bash

# Run all three client instances in parallel
python3 modbusClientWrite.py data-part1.csv 192.168.2.6 1024 &
python3 modbusClientWrite.py data-part2.csv 192.168.2.7 1025 &
python3 modbusClientWrite.py data-part3.csv 192.168.2.8 1026 &

# Wait for all background processes to finish
wait
