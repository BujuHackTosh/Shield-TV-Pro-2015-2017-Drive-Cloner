import os
import subprocess
import struct
import zlib
from tkinter import *
from tkinter import messagebox, filedialog, ttk
import threading

class SATVCloneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shield TV Pro 2015/2017 Drive Cloner")
        self.root.geometry("600x550")

        # Drive Selection Frame
        self.drive_label = Label(self.root, text="Select Drive to Work On:")
        self.drive_label.pack(pady=10)

        self.drive_button = Button(self.root, text="List Drives", command=self.list_drives)
        self.drive_button.pack(pady=5)

        self.drive_listbox = Listbox(self.root, width=50, height=5)
        self.drive_listbox.pack(pady=5)

        # Progress bars
        self.partition_progress = ttk.Progressbar(self.root, orient=HORIZONTAL, length=400, mode='determinate')
        self.partition_progress.pack(pady=10)
        
        self.gpt_progress = ttk.Progressbar(self.root, orient=HORIZONTAL, length=400, mode='determinate')
        self.gpt_progress.pack(pady=10)

        # Actions Frame
        self.dump_button = Button(self.root, text="Dump Partitions", command=self.dump_partitions)
        self.dump_button.pack(pady=5)

        self.insert_drive_label = Label(self.root, text="Insert new drive and click 'List Drives' to select the new drive:")
        self.insert_drive_label.pack(pady=10)
        self.insert_drive_label.config(state=DISABLED)  # Initially disabled

        self.select_new_drive_button = Button(self.root, text="Select New Drive for Dumping", command=self.select_new_drive)
        self.select_new_drive_button.pack(pady=5)
        self.select_new_drive_button.config(state=DISABLED)  # Initially disabled

        self.disk_size_label = Label(self.root, text="Disk Size (in bytes):")
        self.disk_size_label.pack(pady=10)
        self.disk_size_entry = Entry(self.root, state='readonly')  # Set to read-only initially
        self.disk_size_entry.pack(pady=5)

        self.modify_button = Button(self.root, text="Modify GPT Header", command=self.modify_gpt_header)
        self.modify_button.pack(pady=5)
        self.modify_button.config(state=DISABLED)  # Initially disabled

        self.write_button = Button(self.root, text="Write to New Drive", command=self.write_both_parts_to_new_drive)
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
        """Dump the first 6,899,870 blocks and the last 5120 bytes of the drive with progress."""
        def run_dump():
            try:
                selected_drive = self.drive_listbox.get(ACTIVE).split()[0]
                self.drive = selected_drive

                # Estimated block count for the progress bar
                total_blocks = 6899870

                # Dump the first 6,899,870 blocks with progress update
                self.partition_progress["maximum"] = total_blocks
                proc = subprocess.Popen(['dd', f'if={self.drive}', 'of=firstpart.bin', 'count=6899870', 'status=progress'], 
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                # Monitor progress from dd output
                while proc.poll() is None:
                    output = proc.stdout.readline().decode('utf-8')
                    if "records in" in output:
                        completed_blocks = int(output.split()[0])
                        self.partition_progress["value"] = completed_blocks
                    self.root.update_idletasks()

                # Dump the last 5120 bytes
                subprocess.run(['dd', f'if={self.drive}', 'of=lastpart.bin', 'bs=512', 'skip=976773158'], check=True)

                messagebox.showinfo("Success", "Partitions dumped successfully.")
                self.insert_drive_label.config(state=NORMAL)
                self.select_new_drive_button.config(state=NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to dump partitions: {e}")

        # Run dump in a separate thread to keep UI responsive
        threading.Thread(target=run_dump).start()

    def select_new_drive(self):
        """Select a new drive where the modified files will be dumped."""
        try:
            # Select the new drive from the listbox
            selected_new_drive = self.drive_listbox.get(ACTIVE).split()[0]
            self.new_drive = selected_new_drive

            # Extract the size of the new drive
            result = subprocess.run(['fdisk', '-l', self.new_drive], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fdisk_output = result.stdout.decode('utf-8')

            for line in fdisk_output.splitlines():
                if "Disk" in line and "bytes" in line:
                    disk_size = int(line.split()[4])
                    self.disk_size_entry.config(state=NORMAL)
                    self.disk_size_entry.delete(0, END)
                    self.disk_size_entry.insert(0, str(disk_size))
                    self.disk_size_entry.config(state='readonly')
                    break

            self.modify_button.config(state=NORMAL)
            self.write_button.config(state=NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select new drive: {e}")

    def modify_gpt_header(self):
        """Modify GPT header and CRC32 values."""
        try:
            new_disk_size_str = self.disk_size_entry.get()

            if not new_disk_size_str.isdigit():
                messagebox.showerror("Invalid Input", "Please enter a valid disk size in bytes.")
                return

            new_disk_size = int(new_disk_size_str)
            self.total_blocks = new_disk_size // 512

            with open('lastpart.bin', 'rb+') as f:
                data = f.read()
                last_lba_offset = 0xFA8
                last_lba_value = struct.pack('<I', self.total_blocks)
                f.seek(last_lba_offset)
                f.write(last_lba_value)

                crc32_offset = 0x1258
                partition_data = data[:0xFF0]
                crc32_checksum = struct.pack('<I', zlib.crc32(partition_data))
                f.seek(crc32_offset)
                f.write(crc32_checksum)

            messagebox.showinfo("Success", "GPT header modified successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify GPT header: {e}")

    def write_both_parts_to_new_drive(self):
        """Write the firstpart.bin and modified lastpart.bin to the new drive with progress."""
        def run_write():
            try:
                # Write firstpart.bin (6,899,870 blocks) to the new drive
                total_firstpart_blocks = 6899870  # Blocks to write from firstpart.bin
                self.partition_progress["maximum"] = total_firstpart_blocks

                proc1 = subprocess.Popen(['dd', 'if=firstpart.bin', f'of={self.new_drive}', 'bs=512', 'count=6899870', 'status=progress'],
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                # Monitor progress for firstpart.bin write
                while proc1.poll() is None:
                    output = proc1.stdout.readline().decode('utf-8')
                    if "records in" in output:
                        completed_blocks = int(output.split()[0])
                        self.partition_progress["value"] = completed_blocks
                    self.root.update_idletasks()

                # Write lastpart.bin (5120 bytes) to the new drive
                last_block = self.total_blocks - 10
                total_size = 5120  # Bytes to write from lastpart.bin

                self.gpt_progress["maximum"] = total_size

                proc2 = subprocess.Popen(['dd', 'if=lastpart.bin', f'of={self.new_drive}', 'bs=512', f'seek={last_block}', 'status=progress'], 
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                # Monitor progress for lastpart.bin write
                while proc2.poll() is None:
                    output = proc2.stdout.readline().decode('utf-8')
                    if "bytes" in output and "written" in output:
                        written_bytes = int(output.split()[0])
                        self.gpt_progress["value"] = written_bytes
                    self.root.update_idletasks()
