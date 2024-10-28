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



## User Guide for Shield TV Pro 2015/2017 Drive Cloner

This guide will walk you through using the Shield TV Pro 2015/2017 Drive Cloner application to copy the partition layout from one drive to another. 

**Important Note:**

* This program modifies drive partitions and can potentially lead to data loss. **Ensure you have a proper backup of your data before proceeding.**
* This program is designed for Shield TV Pro 2015/2017 models. Using it on other devices might not work as intended.

**Requirements:**

* A Linux computer with Python 3 installed.
* The `fdisk` command-line tool (usually pre-installed on most Linux systems).
* The `tkinter` library for Python (you can install it using `pip install tkinter`).

**Steps:**

1. **Download and Run the Application:**

  * Download the Shield TV Pro 2015/2017 Drive Cloner application files.
  * Open a terminal or command prompt and navigate to the directory containing the downloaded files.
  * Run the program

2. **List Available Drives:**

  * The application window will appear. Click the "List Drives" button.

  * This will display a list of all available drives detected by your system in the listbox. 

3. **Select the Drive to Clone From:**

  * In the listbox, select the drive that contains the partition layout you want to copy.

4. **Dump Partitions:**

  * Click the "Dump Partitions" button.

  * This will perform two actions:
      * It will extract the first 6,899,870 blocks of data from the selected drive and save it to a file named `firstpart.bin`.
      * It will extract the last 5120 bytes of the drive containing the partition table and GPT header and save it to a file named `lastpart.bin`. 

  * If successful, a message will pop up indicating that the partitions have been dumped successfully.

5. **Insert the New Drive:**

  * Insert the new drive where you want to copy the partition layout.

6. **Refresh Drive List:**

  * Click the "List Drives" button again to refresh the list and ensure the new drive is detected.

7. **Select the New Drive:**

  * In the listbox, select the newly inserted drive.

8. **Get New Drive Size:**

  * Click the "Select New Drive for Dumping" button.

  * This will automatically extract the size of the new drive and display it in the "Disk Size" field.

9. **Modify GPT Header (Optional):**

  * This step is optional but very crucial for drives of different sizes. If the new drive has a different size than the original drive, the partition table will need adjustments.

    * **Enter the new disk size:** In the "Disk Size" field, ensure the displayed size accurately reflects the size of the new drive bytes. You can find the size information on the drive's label or through the manufacturer's specifications.

  * Click the "Modify GPT Header" button.

  * This will modify the `lastpart.bin` file according to the new drive size, specifically:
      * It will update the "Last LBA" value in the GPT header to reflect the total number of blocks on the new drive.
      * It will recalculate and update the CRC32 checksum for the partition data to ensure data integrity.

  * If successful, a message will pop up indicating that the GPT header has been modified successfully.

10. **Write Modified Partition Table:**

  * Click the "Write Modified GPT Header" button.

  * This will write the modified `lastpart.bin` file containing the adjusted partition table to the last block of the new drive.

  * If successful, a message will pop up indicating that the `lastpart.bin` file has been written to the drive successfully.


**Additional Notes:**

* This program provides a basic process for cloning drive partitions. It's recommended to have a good understanding of GPT partitions and data recovery procedures before attempting this process. 
* Always ensure you have a proper backup of your data before making any modifications to your drives.
