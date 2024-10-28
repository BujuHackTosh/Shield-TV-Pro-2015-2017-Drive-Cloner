import os
import subprocess
import struct
import zlib
from tkinter import *
from tkinter import messagebox, filedialog

# Main Application class
class SATVCloneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shield TV Pro 2015/2017 Drive Cloner")  # Updated title
        self.root.geometry("600x500")

        # Drive Selection Frame
        self.drive_label = Label(self.root, text="Select Drive to Work On:")
        self.drive_label.pack(pady=10)

        self.drive_button = Button(self.root, text="List Drives", command=self.list_drives)
        self.drive_button.pack(pady=5)

        self.drive_listbox = Listbox(self.root, width=50, height=5)
        self.drive_listbox.pack(pady=5)

        # Actions Frame
        self.dump_button = Button(self.root, text="Dump Partitions", command=self.dump_partitions)
        self.dump_button.pack(pady=5)

        self.insert_drive_label = Label(self.root, text="Insert new drive and click 'List Drives' to select the new drive:")
        self.insert_drive_label.pack(pady=10)
        self.insert_drive_label.config(state=DISABLED)  # Initially disabled

        self.select_new_drive_button = Button(self.root, text="Select New Drive for Dumping", command=self.select_new_drive)
        self.select_new_drive_button.pack(pady=5)
        self.select_new_drive_button.config(state=DISABLED)  # Initially disabled

        # Disk size input (automatically populated later)
        self.disk_size_label = Label(self.root, text="Disk Size (in bytes):")
        self.disk_size_label.pack(pady=10)
        self.disk_size_entry = Entry(self.root, state='readonly')  # Set to read-only initially
        self.disk_size_entry.pack(pady=5)

        self.modify_button = Button(self.root, text="Modify GPT Header", command=self.modify_gpt_header)
        self.modify_button.pack(pady=5)
        self.modify_button.config(state=DISABLED)  # Initially disabled

        self.write_button = Button(self.root, text="Write Modified GPT Header", command=self.write_modified_lastpart)
        self.write_button.pack(pady=5)
        self.write_button.config(state=DISABLED)  # Initially disabled

        self.total_blocks = 0
        self.drive = ""
        self.new_drive = ""

    def list_drives(self):
        """List available drives using fdisk -l."""
        try:
            result = subprocess.run(['fdisk', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            drives_output = result.stdout.decode('utf-8')

            # Parse drive names
            self.drive_listbox.delete(0, END)  # Clear previous entries
            for line in drives_output.splitlines():
                if line.startswith("/dev/"):
                    self.drive_listbox.insert(END, line)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list drives: {e}")

    def dump_partitions(self):
        """Dump the first 6,899,870 blocks and the last 5120 bytes of the drive."""
        try:
            selected_drive = self.drive_listbox.get(ACTIVE).split()[0]
            self.drive = selected_drive

            # Dump the first 6,899,870 blocks
            subprocess.run(['dd', f'if={self.drive}', 'of=firstpart.bin', 'count=6899870'], check=True)

            # Dump the last 5120 bytes containing partition array and GPT header
            subprocess.run(['dd', f'if={self.drive}', 'of=lastpart.bin', 'bs=512', 'skip=976773158'], check=True)

            messagebox.showinfo("Success", "Partitions dumped successfully.")

            # Enable new instructions and buttons to insert and select new drive
            self.insert_drive_label.config(state=NORMAL)
            self.select_new_drive_button.config(state=NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to dump partitions: {e}")

    def select_new_drive(self):
        """Select a new drive where the modified files will be dumped."""
        try:
            # Select the new drive from the listbox
            selected_new_drive = self.drive_listbox.get(ACTIVE).split()[0]
            self.new_drive = selected_new_drive

            # Extract the size of the new drive
            result = subprocess.run(['fdisk', '-l', self.new_drive], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fdisk_output = result.stdout.decode('utf-8')

            # Find the disk size in bytes
            for line in fdisk_output.splitlines():
                if "Disk" in line and "bytes" in line:
                    disk_size = int(line.split()[4])  # Extract the size in bytes
                    self.disk_size_entry.config(state=NORMAL)  # Temporarily make it editable
                    self.disk_size_entry.delete(0, END)
                    self.disk_size_entry.insert(0, str(disk_size))  # Auto-fill the size in bytes
                    self.disk_size_entry.config(state='readonly')  # Set back to read-only
                    break

            # Enable modification and writing once new drive is selected
            self.modify_button.config(state=NORMAL)
            self.write_button.config(state=NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select new drive: {e}")

    def modify_gpt_header(self):
        """Modify GPT header and CRC32 values."""
        try:
            # Retrieve the new disk size entered by the user
            new_disk_size_str = self.disk_size_entry.get()

            # Validate that the input is a valid number
            if not new_disk_size_str.isdigit():
                messagebox.showerror("Invalid Input", "Please enter a valid disk size in bytes.")
                return

            # Convert the valid string to an integer
            new_disk_size = int(new_disk_size_str)

            # Calculate total blocks (disk size divided by block size 512)
            self.total_blocks = new_disk_size // 512

            # Open the lastpart.bin file for modification
            with open('lastpart.bin', 'rb+') as f:
                data = f.read()

                # Modify the Last LBA (offset 0xFA8) in reverse byte order
                last_lba_offset = 0xFA8
                last_lba_value = struct.pack('<I', self.total_blocks)  # Little-endian
                f.seek(last_lba_offset)
                f.write(last_lba_value)

                # Modify CRC32 value at offset 0x1258
                crc32_offset = 0x1258
                partition_data = data[:0xFF0]  # Select data up to the partition table
                crc32_checksum = struct.pack('<I', zlib.crc32(partition_data))
                f.seek(crc32_offset)
                f.write(crc32_checksum)

            messagebox.showinfo("Success", "GPT header modified successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify GPT header: {e}")

    def write_modified_lastpart(self):
        """Write the modified lastpart.bin to the drive."""
        try:
            last_block = self.total_blocks - 10
            subprocess.run(['dd', 'if=lastpart.bin', f'of={self.new_drive}', 'bs=512', f'seek={last_block}'], check=True)
            messagebox.showinfo("Success", "lastpart.bin written to the drive successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write lastpart.bin: {e}")


# Run the application
if __name__ == "__main__":
    root = Tk()
    app = SATVCloneApp(root)
    root.mainloop()
