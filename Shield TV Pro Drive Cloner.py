import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import struct
import zlib
from subprocess import check_output, Popen, PIPE
import threading

def list_disks():
    """List all disks available on the system and display them in the disk list."""
    output = check_output(["lsblk", "-o", "NAME,SIZE,TYPE", "-d"]).decode()
    disks = [line for line in output.splitlines() if "disk" in line]
    disk_list.delete(0, tk.END)
    for disk in disks:
        disk_list.insert(tk.END, disk)

def run_dd(command, progress_label, max_blocks, update_progress, stop_event):
    """Run dd command and update progress with cancellation support."""
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    for line in process.stderr:
        if stop_event.is_set():
            process.terminate()
            progress_label.set("Process cancelled.")
            return False
        if b"records in" in line:
            progress_label.set(line.decode("utf-8").strip())
            progress_data = line.decode("utf-8").split()
            blocks_copied = int(progress_data[0]) if progress_data[0].isdigit() else 0
            update_progress(blocks_copied, max_blocks)
    process.wait()
    return process.returncode == 0

def update_progress_bar(value, maximum):
    """Update progress bar and percentage label."""
    progress_bar["maximum"] = maximum
    progress_bar["value"] = value
    percentage = int((value / maximum) * 100) if maximum > 0 else 0
    progress_percentage_label.config(text=f"{percentage}%")

def confirm_action(action_name, action_func):
    """Confirm critical actions with the user."""
    response = messagebox.askyesno("Confirm Action", f"Are you sure you want to {action_name}? This may result in data loss.")
    if response:
        action_func()

def modify_lastpart(bin_file, new_disk_size):
    """Modify the lastpart.bin file according to the provided specifications."""
    # Calculate the last LBA based on the new disk size
    last_lba = (new_disk_size // 512) - 1  # LBA is based on 512-byte blocks

    # Open the lastpart.bin file for reading and writing
    with open(bin_file, 'r+b') as f:
        # Read the whole file into memory
        data = f.read()

        # Step 1: Update Last LBA (offset 0xFA8)
        last_lba_offset = 0xFA8
        last_lba_bytes = struct.pack('<I', last_lba)  # Pack as little-endian
        data = data[:last_lba_offset] + last_lba_bytes + data[last_lba_offset + 4:]

        # Step 2: Calculate CRC32 for the partition array
        partition_array_offset = 0x0  # Adjust as necessary
        partition_array_length = 0xFF0  # Adjust as necessary
        crc_data = data[partition_array_offset:partition_array_offset + partition_array_length]
        crc32_value = zlib.crc32(crc_data) & 0xffffffff  # Ensure it is unsigned
        crc_bytes = struct.pack('<I', crc32_value)

        # Step 3: Update CRC32 in the GPT header (offset 0x1258)
        crc_offset = 0x1258
        data = data[:crc_offset] + crc_bytes[::-1] + data[crc_offset + 4:]

        # Step 4: Update other GPT header values (example values, adjust as necessary)
        gpt_header_offset = 0x1218
        data = data[:gpt_header_offset] + struct.pack('<I', last_lba)[::-1] + data[gpt_header_offset + 4:]

        # Update Last Usable LBA and Starting LBA of array of partition entries (dummy values used here)
        last_usable_lba_offset = 0x1230  # Adjust this offset as necessary
        starting_lba_offset = 0x1248  # Adjust this offset as necessary
        data = data[:last_usable_lba_offset] + struct.pack('<I', last_lba)[::-1] + data[last_usable_lba_offset + 4:]
        data = data[:starting_lba_offset] + struct.pack('<I', 2)[::-1] + data[starting_lba_offset + 4:]

        # Final CRC32 of the GPT header
        gpt_crc_offset = 0x1210
        data = data[:gpt_crc_offset] + b'\x00\x00\x00\x00' + data[gpt_crc_offset + 4:]
        new_gpt_crc = zlib.crc32(data[gpt_header_offset:gpt_crc_offset]) & 0xffffffff
        data = data[:gpt_crc_offset] + struct.pack('<I', new_gpt_crc)[::-1] + data[gpt_crc_offset + 4:]

        # Write the modified data back to the file
        f.seek(0)
        f.write(data)

def write_lastpart_to_disk(bin_file, target_disk, total_blocks):
    """Write the modified lastpart.bin to the specified location on the new disk."""
    lastpart_blocks = 10  # lastpart.bin size in blocks (10 blocks of 512 bytes)
    seek_position = total_blocks - lastpart_blocks  # Calculate seek position
    command = f"dd if={bin_file} of={target_disk} bs=512 seek={seek_position}"
    
    # Run the dd command
    os.system(command)

def dump_partitions():
    """Dump partitions from the selected drive."""
    selected_disk = disk_list.get(tk.ACTIVE).split()[0]
    if not selected_disk:
        messagebox.showerror("Error", "No drive selected.")
        return

    def _dump_partitions():
        # Disable dump button and enable cancel button
        dump_button.config(state=tk.DISABLED)
        cancel_button.config(state=tk.NORMAL)

        stop_event.clear()

        max_blocks_first = 6899870
        max_blocks_last = 10

        progress_label.set("Dumping first part...")
        update_progress_bar(0, max_blocks_first)
        if run_dd(f"dd if=/dev/{selected_disk} of=firstpart.bin bs=512 count=6899870", progress_label, max_blocks_first, update_progress_bar, stop_event):
            log_message("First part dumped successfully.")
        else:
            log_message("Failed to dump the first part or cancelled.")
            dump_button.config(state=tk.NORMAL)
            cancel_button.config(state=tk.DISABLED)
            return

        progress_label.set("Dumping last part...")
        update_progress_bar(0, max_blocks_last)
        total_sectors = int(check_output(["fdisk", "-l", f"/dev/{selected_disk}"]).decode().split()[-1])
        if run_dd(f"dd if=/dev/{selected_disk} of=lastpart.bin bs=512 skip={total_sectors - 10} count=10", progress_label, max_blocks_last, update_progress_bar, stop_event):
            log_message("Last part dumped successfully.")
            # Modify lastpart.bin after dumping
            modify_lastpart('lastpart.bin', total_sectors * 512)
        else:
            log_message("Failed to dump the last part or cancelled.")
            dump_button.config(state=tk.NORMAL)
            cancel_button.config(state=tk.DISABLED)
            return

        progress_bar["value"] = 0
        dump_button.config(state=tk.DISABLED)
        select_clone_button.config(state=tk.NORMAL)
        cancel_button.config(state=tk.DISABLED)

    confirm_action("dump partitions", _dump_partitions)

def log_message(message):
    """Log messages to the logging window."""
    log_text.configure(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_text.configure(state=tk.DISABLED)

def cancel_operation():
    """Cancel the current operation."""
    stop_event.set()

# GUI setup with Frames and better organization
root = tk.Tk()
root.title("Disk Clone Utility")

# Global variables
progress_label = tk.StringVar()
stop_event = threading.Event()

# Frames for layout
disk_frame = tk.Frame(root)
disk_frame.grid(row=0, column=0, padx=10, pady=10)

progress_frame = tk.Frame(root)
progress_frame.grid(row=1, column=0, padx=10, pady=10)

log_frame = tk.Frame(root)
log_frame.grid(row=2, column=0, padx=10, pady=10)

button_frame = tk.Frame(root)
button_frame.grid(row=3, column=0, padx=10, pady=10)

# Disk list
disk_list = tk.Listbox(disk_frame, height=6, width=50)
disk_list.grid(row=0, column=0, padx=10, pady=5)

list_button = tk.Button(disk_frame, text="List Disks", command=list_disks)
list_button.grid(row=0, column=1, padx=10, pady=5)

# Progress bar, percentage label, and label for progress text
progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
progress_bar.grid(row=0, column=0,
