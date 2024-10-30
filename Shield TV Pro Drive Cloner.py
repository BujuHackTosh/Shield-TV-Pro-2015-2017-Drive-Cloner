import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import struct
import zlib
from subprocess import check_output, Popen, PIPE

def list_disks():
    """List all disks available on the system and display them in the disk list."""
    output = check_output(["lsblk", "-o", "NAME,SIZE,TYPE", "-d"]).decode()
    disks = [line for line in output.splitlines() if "disk" in line]
    disk_list.delete(0, tk.END)
    for disk in disks:
        disk_list.insert(tk.END, disk)

def run_dd(command, progress_label, max_blocks, update_progress):
    """Run dd command and update progress."""
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    for line in process.stderr:
        if b"records in" in line:
            progress_label.set(line.decode("utf-8").strip())
            # Update the progress bar
            progress_data = line.decode("utf-8").split()
            blocks_copied = int(progress_data[0]) if progress_data[0].isdigit() else 0
            update_progress(blocks_copied, max_blocks)

    process.wait()
    return process.returncode == 0

def dump_partitions():
    """Dump partitions from the selected drive."""
    selected_disk = disk_list.get(tk.ACTIVE).split()[0]
    if not selected_disk:
        messagebox.showerror("Error", "No drive selected.")
        return

    # Set the maximum for the progress bar for the dump process
    max_blocks_first = 6899870
    max_blocks_last = 10

    # Dump first 6,899,870 blocks
    progress_label.set("Dumping first part...")
    update_progress_bar(0, max_blocks_first)
    if run_dd(f"dd if=/dev/{selected_disk} of=firstpart.bin bs=512 count=6899870", progress_label, max_blocks_first, update_progress_bar):
        messagebox.showinfo("Success", "First part dumped successfully.")
    else:
        messagebox.showerror("Error", "Failed to dump the first part.")
        return

    # Dump last 5120 bytes (10 blocks of 512 bytes each)
    progress_label.set("Dumping last part...")
    update_progress_bar(0, max_blocks_last)
    total_sectors = int(check_output(["fdisk", "-l", f"/dev/{selected_disk}"]).decode().split()[-1])
    if run_dd(f"dd if=/dev/{selected_disk} of=lastpart.bin bs=512 skip={total_sectors - 10} count=10", progress_label, max_blocks_last, update_progress_bar):
        messagebox.showinfo("Success", "Last part dumped successfully.")
    else:
        messagebox.showerror("Error", "Failed to dump the last part.")
        return

    progress_bar["value"] = 0  # Reset the progress bar
    dump_button.config(state=tk.DISABLED)
    select_clone_button.config(state=tk.NORMAL)

def get_disk_info(disk_path):
    """Get sector count and sector size from the disk using fdisk command."""
    output = check_output(["fdisk", "-l", disk_path]).decode()
    sectors = int([line for line in output.splitlines() if "sectors" in line][0].split()[7])
    sector_size = int([line for line in output.splitlines() if "bytes" in line][0].split()[8])
    return sectors, sector_size

def calculate_last_usable_lba(sectors):
    """Calculate the last usable LBA as (sectors - 34)."""
    return sectors - 34

def convert_to_reverse_hex(value):
    """Convert integer value to a reversed hexadecimal byte sequence."""
    hex_value = struct.pack("<I", value)  # Little-endian unsigned int
    return hex_value

def update_lastpart_bin(lastpart_path, last_usable_lba):
    """Update the Last Usable LBA in lastpart.bin."""
    with open(lastpart_path, "rb+") as f:
        f.seek(0xFA8)
        f.write(convert_to_reverse_hex(last_usable_lba))

def calculate_crc32(data):
    """Calculate CRC-32 checksum."""
    return struct.pack("<I", zlib.crc32(data) & 0xFFFFFFFF)

def update_partition_array_crc(lastpart_path):
    """Calculate and update the CRC-32 of the partition array in lastpart.bin."""
    with open(lastpart_path, "rb+") as f:
        f.seek(0)  # Start at beginning of file
        partition_array = f.read(0x100)  # Read up to offset 0xFF
        crc32_value = calculate_crc32(partition_array)

        # Write the CRC-32 to GPT header at offset 0x1258
        f.seek(0x1258)
        f.write(crc32_value[::-1])  # Reverse bytes for big-endian storage

def update_gpt_header(lastpart_path, sectors):
    """Update the GPT header values in lastpart.bin to reflect the new disk layout."""
    with open(lastpart_path, "rb+") as f:
        # Update positions of GPT header and backup
        gpt_header_position = 1
        backup_header_position = sectors - 1
        f.seek(0x1218)
        f.write(convert_to_reverse_hex(gpt_header_position))
        f.seek(0x1220)
        f.write(convert_to_reverse_hex(backup_header_position))

        # Update Last Usable LBA
        last_usable_lba = calculate_last_usable_lba(sectors)
        f.seek(0x1230)
        f.write(convert_to_reverse_hex(last_usable_lba))

        # Update Starting LBA of partition array entries
        starting_lba = 2
        f.seek(0x1248)
        f.write(convert_to_reverse_hex(starting_lba))

def update_gpt_header_crc(lastpart_path):
    """Calculate and update the CRC-32 of the GPT header itself."""
    with open(lastpart_path, "rb+") as f:
        # Clear the existing CRC-32 at offset 0x1210
        f.seek(0x1210)
        f.write(b"\x00\x00\x00\x00")

        # Calculate CRC-32 of the GPT header (from 0x1200 to last non-zero byte before zeros)
        f.seek(0x1200)
        gpt_header = f.read(0x5C)  # Length depends on actual header size; 0x5C in this example
        crc32_value = calculate_crc32(gpt_header)

        # Write the CRC-32 to GPT header at offset 0x1210
        f.seek(0x1210)
        f.write(crc32_value)

def modify_gpt_header():
    """Modify GPT header for the new disk size."""
    new_disk = disk_list.get(tk.ACTIVE).split()[0]
    if not new_disk:
        messagebox.showerror("Error", "No new drive selected.")
        return

    sectors, sector_size = get_disk_info(f"/dev/{new_disk}")
    update_lastpart_bin("lastpart.bin", calculate_last_usable_lba(sectors))
    update_partition_array_crc("lastpart.bin")
    update_gpt_header("lastpart.bin", sectors)
    update_gpt_header_crc("lastpart.bin")

    messagebox.showinfo("Success", "GPT header modified for new disk.")

def write_partition_files():
    """Write firstpart.bin and modified lastpart.bin to the new drive."""
    new_disk = disk_list.get(tk.ACTIVE).split()[0]
    if not new_disk:
        messagebox.showerror("Error", "No new drive selected.")
        return

    max_blocks_first = 6899870
    max_blocks_last = 10

    # Write firstpart.bin
    progress_label.set("Writing first part...")
    update_progress_bar(0, max_blocks_first)
    if run_dd(f"dd if=firstpart.bin of=/dev/{new_disk} bs=512 seek=0", progress_label, max_blocks_first, update_progress_bar):
        messagebox.showinfo("Success", "First part written successfully.")
    else:
        messagebox.showerror("Error", "Failed to write the first part.")
        return

    # Write lastpart.bin
    progress_label.set("Writing last part...")
    update_progress_bar(0, max_blocks_last)
    total_sectors = int(check_output(["fdisk", "-l", f"/dev/{new_disk}"]).decode().split()[-1])
    if run_dd(f"dd if=lastpart.bin of=/dev/{new_disk} bs=512 seek={total_sectors - 10}", progress_label, max_blocks_last, update_progress_bar):
        messagebox.showinfo("Success", "Last part written successfully.")
    else:
        messagebox.showerror("Error", "Failed to write the last part.")
        return

    messagebox.showinfo("Success", "Cloning complete.")

def update_progress_bar(value, maximum):
    """Update progress bar."""
    progress_bar["maximum"] = maximum
    progress_bar["value"] = value

# GUI setup
root = tk.Tk()
root.title("Disk Clone Utility")

# List disks
disk_list_frame