# Shield-TV-Pro-2015-2017-Drive-Cloner
This repository contains the source code for a Shield TV Pro 2015/2017 Drive Cloner application written in Python with a Tkinter GUI
This repository contains the source code for a Shield TV Pro 2015/2017 Drive Cloner application written in Python with a Tkinter GUI.

Features:

Lists available drives using fdisk -l.
Dumps the first 6,899,870 blocks and the last 5120 bytes of the selected drive.
Allows selection of a new drive for dumping the modified partition table.
Calculates the total number of blocks based on the new drive size.
Modifies the GPT header (Last LBA) and CRC32 values in the lastpart.bin file.
Writes the modified lastpart.bin to the last block of the new drive.
Requirements:

Python 3
fdisk command-line tool
tkinter library
Disclaimer:

This application is provided for educational purposes only. Modifying drive partitions can be risky and lead to data loss. Use this tool at your own discretion and ensure you have a proper backup before proceeding.
