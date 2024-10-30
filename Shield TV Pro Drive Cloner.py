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
progress_bar.grid(row=0, column=0, padx=10, pady=5)

progress_percentage_label = tk.Label(progress_frame, text="0%")
progress_percentage_label.grid(row=0, column=1, padx=10, pady=5)

progress_label_widget = tk.Label(progress_frame, textvariable=progress_label)
progress_label_widget.grid(row=1, column=0, padx=10, pady=5)

# Log window
log_text = tk.Text(log_frame, height=10, width=60, state=tk.DISABLED)
log_text.grid(row=0, column=0, padx=10, pady=5)

# Buttons
dump_button = tk.Button(button_frame, text="Dump Partitions", command=dump_partitions)
dump_button.grid(row=0, column=0, padx=10, pady=5)

cancel_button = tk.Button(button_frame, text="Cancel", command=cancel_operation, state=tk.DISABLED)
cancel_button.grid(row=0, column=1, padx=10, pady=5)

select_clone_button = tk.Button(button_frame, text="Select Clone", state=tk.DISABLED)
select_clone_button.grid(row=0, column=2, padx=10, pady=5)

help_button = tk.Button(button_frame, text="Help", command=lambda: messagebox.showinfo("Help", "This tool helps in cloning disks. Use 'List Disks' to select disks."))
help_button.grid(row=0, column=3, padx=10, pady=5)

# Final setup
list_disks()
root.mainloop()
