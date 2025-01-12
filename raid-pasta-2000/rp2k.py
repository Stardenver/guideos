#!/usr/bin/python3

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess

def install_mdadm():
    try:
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'mdadm'], check=True)
        messagebox.showinfo("Erfolg", "mdadm erfolgreich installiert.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler bei der Installation von mdadm: {e}")

def list_drives():
    try:
        result = subprocess.run(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'], capture_output=True, text=True, check=True)
        drives = result.stdout.splitlines()[1:]  # Skip header line
        for drive in drives:
            if 'disk' in drive:
                drive_info = drive.split()
                drive_name = f"/dev/{drive_info[0]}"
                drive_size = drive_info[1]
                mount_point = drive_info[3] if len(drive_info) > 3 else ""
                drive_var = tk.BooleanVar()
                drives_list.append((drive_name, drive_size, mount_point, drive_var))
                state = tk.NORMAL if not mount_point else tk.DISABLED
                drive_checkbtn = ttk.Checkbutton(left_frame, text=f"{drive_name} ({drive_size})", variable=drive_var, state=state)
                drive_checkbtn.pack(anchor='w')
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler beim Auflisten der Laufwerke: {e}")

def create_raid():
    raid_level = raid_level_var.get()
    selected_drives = [drive[0] for drive in drives_list if drive[3].get()]
    
    if not selected_drives:
        messagebox.showerror("Fehler", "Bitte wählen Sie mindestens ein Laufwerk aus.")
        return

    try:
        command = ['sudo', 'mdadm', '--create', '/dev/md0', '--level', raid_level, '--raid-devices', str(len(selected_drives))] + selected_drives
        subprocess.run(command, check=True)
        messagebox.showinfo("Erfolg", "RAID-Array erfolgreich erstellt.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler beim Erstellen des RAID-Arrays: {e}")

# GUI Setup
root = tk.Tk()
root.title("RAID-Array Ersteller")
root.geometry("800x400")

# Style configuration
style = ttk.Style()
style.configure("TLabel", background="black", foreground="white")
style.configure("TButton", background="black", foreground="white")
style.configure("TCheckbutton", background="black", foreground="white")
style.configure("TOptionMenu", background="black", foreground="white")
root.config(background="black")

# Frames für Layout
left_frame = tk.Frame(root, bg='black')
left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

right_frame = tk.Frame(root, bg='black')
right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

install_button = ttk.Button(left_frame, text="mdadm installieren", command=install_mdadm)
install_button.pack(pady=5)

drives_list = []

label = ttk.Label(left_frame, text="RAID-Level:")
label.pack(pady=5)
raid_level_var = tk.StringVar(value="1")
raid_level_dropdown = ttk.OptionMenu(left_frame, raid_level_var, "1", "0", "1", "5", "6", "10")
raid_level_dropdown.pack(pady=5)

create_button = ttk.Button(left_frame, text="RAID-Array erstellen", command=create_raid)
create_button.pack(pady=5)

# RAID-Info Labels
raid_info_label = ttk.Label(right_frame, text="RAID-Level Informationen:", background='black', foreground='white', font=('Helvetica', 12, 'bold'))
raid_info_label.pack(pady=5, anchor='w')

raid_info = {
    "0": "RAID 0: Striping - Keine Redundanz, Höhere Geschwindigkeit.",
    "1": "RAID 1: Mirroring - Daten werden gespiegelt, hohe Zuverlässigkeit.",
    "5": "RAID 5: Block-Level Striping mit verteiltem Paritätsbit - Gute Leistung, effizienter Speicherplatz.",
    "6": "RAID 6: Block-Level Striping mit doppeltem Paritätsbit - Höhere Redundanz als RAID 5.",
    "10": "RAID 10: Kombination aus RAID 1 und RAID 0 - Hohe Performance und Redundanz."
}

for level, info in raid_info.items():
    info_label = ttk.Label(right_frame, text=f"RAID {level}: {info}", wraplength=300, background='black', foreground='white', justify=tk.LEFT)
    info_label.pack(pady=2, anchor='w')

# List drives automatically on startup
list_drives()

root.mainloop()
