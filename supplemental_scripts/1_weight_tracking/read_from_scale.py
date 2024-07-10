import serial
import sys
import os

device = sys.argv[1]
out_tsv = sys.argv[2]

open(out_tsv, "a")

with open(out_tsv, "r") as file:
    content = file.readlines()

if len(content) > 0:
    current_id = int(content[-1].split("\t")[0]) + 1
    print("Current ID: " + str(current_id))
else:
    current_id = 1
    print("Empty file")

ser = serial.Serial(device)

while True:
    with open(out_tsv, "a") as file:
        ser.flush()
        value = float(ser.readline()[4:13])
        print(str(current_id) + "\t" + str(value))
        #beep.play()
        file.write(str(current_id) + "\t" + str(value) + "\n")
        current_id += 1
