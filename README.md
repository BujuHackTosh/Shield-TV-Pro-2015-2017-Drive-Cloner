# Shield-TV-Pro-2015-2017-Drive-Cloner

# Disk Clone Utility

The Disk Clone Utility is a Python-based application designed to simplify the process of cloning disk partitions. It allows users to create a binary dump of disk partitions and write them to a new disk while providing visual feedback and logging capabilities.

## Features

- **Disk Listing**: Lists all available disks on the system.
- **Partition Dumping**: Dumps partitions from the selected disk.
- **Progress Tracking**: Displays progress in a progress bar and shows the percentage of completion.
- **Cancellation Support**: Allows users to cancel long-running operations.
- **Logging Window**: Provides a history of actions performed along with success and error messages.
- **Help Menu**: Offers guidance on using the application.
- **Confirmation Dialogs**: Warns users about potential data loss before critical operations.

## Requirements

- Python 3.x
- `tkinter` library (usually included with Python)
- Access to the command line utilities like `lsblk` and `fdisk`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/disk-clone-utility.git
   cd disk-clone-utility


Ensure you have Python installed on your system.
Run the application:

python disk_clone_utility.py



Usage

Click the "List Disks" button to view all available disks.
Select the disk you want to clone from the list.
Click "Dump Partitions" to start the dumping process.
Confirm the action when prompted, as it may lead to data loss.
Monitor the progress through the progress bar and percentage display.
Use the "Cancel" button to stop any ongoing operation.
Contributing

If you would like to contribute to the project, feel free to fork the repository and submit a pull request. 
Any improvements, bug fixes, or suggestions are welcome.


