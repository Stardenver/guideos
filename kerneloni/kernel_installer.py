import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO

def add_liquorix_repository():
    try:
        subprocess.run(['sudo', 'sh', '-c', 'echo "deb http://liquorix.net/debian sid main" > /etc/apt/sources.list.d/liquorix.list'], check=True)
        subprocess.run(['wget', '-O', '/tmp/liquorix.key', 'https://liquorix.net/liquorix-keyring.gpg'], check=True)
        subprocess.run(['sudo', 'cp', '/tmp/liquorix.key', '/etc/apt/trusted.gpg.d/liquorix-keyring.gpg'], check=True)
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        messagebox.showinfo("Erfolg", "Liquorix-Repository wurde erfolgreich hinzugefügt.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler beim Hinzufügen des Liquorix-Repositorys: {e}")

def install_kernel(kernel_version):
    if kernel_version == "linux-image-liquorix-amd64":
        add_liquorix_repository()
    try:
        subprocess.run(['sudo', 'apt-get', 'install', '-y', kernel_version], check=True)
        messagebox.showinfo("Erfolg", f"Kernel {kernel_version} wurde erfolgreich installiert.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler bei der Installation des Kernels: {e}")

def on_install_button_click():
    kernel_version = kernel_var.get()
    if kernel_version:
        messagebox.showinfo("Hinweis", "Ein Terminal wird sich öffnen. Möglicherweise müssen Sie die Installation bestätigen und das Root-Passwort eingeben.")
        threading.Thread(target=install_kernel, args=(kernel_version,)).start()
    else:
        messagebox.showwarning("Warnung", "Bitte wählen Sie eine Kernel-Version aus.")

def update_description(*args):
    kernel_version = kernel_var.get()
    description = kernel_descriptions.get(kernel_version, "")
    description_label.config(text=description)

def get_installed_kernel_versions():
    try:
        result = subprocess.run(['dpkg', '--list', 'linux-image-*'], capture_output=True, text=True, check=True)
        kernel_versions = []
        for line in result.stdout.splitlines():
            if line.startswith('ii'):
                parts = line.split()
                if len(parts) > 2 and 'linux-image' in parts[1]:
                    kernel_versions.append((parts[1], parts[2]))
        return kernel_versions
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler beim Abrufen der Kernel-Versionen: {e}")
        return []

# Liste der verfügbaren Kernel-Versionen und ihre Beschreibungen
kernel_versions = [
    ("LTS-Kernel", "linux-image-amd64"),
    ("Realtime-Kernel", "linux-image-rt-amd64"),
    ("Liquorix-Kernel", "linux-image-liquorix-amd64")
]
kernel_descriptions = {
    "linux-image-amd64": "LTS Kernel: Stabil und langfristig unterstützt.",
    "linux-image-rt-amd64": "Real-Time Kernel: Für Echtzeitanwendungen optimiert.",
    "linux-image-liquorix-amd64": "Liquorix Kernel: Für Desktop- und Multimedia-Anwendungen optimiert."
}

# Aktuellen Standard-Debian-Kernel hinzufügen
try:
    result = subprocess.run(['uname', '-r'], capture_output=True, text=True, check=True)
    current_kernel = result.stdout.strip()
    if "liquorix" not in current_kernel:
        kernel_versions.append(("Aktueller Standard-Kernel", f"linux-image-{current_kernel}"))
        kernel_descriptions[f"linux-image-{current_kernel}"] = "Aktueller Standard-Debian-Kernel."
except subprocess.CalledProcessError as e:
    messagebox.showerror("Fehler", f"Fehler beim Abrufen des aktuellen Kernels: {e}")

# Installierte Kernel-Versionen abrufen und hinzufügen
installed_kernels = get_installed_kernel_versions()
for kernel_name, kernel_version in installed_kernels:
    if kernel_name not in [kv[1] for kv in kernel_versions]:
        kernel_versions.append((f"Installierter Kernel: {kernel_name}", kernel_name))
        kernel_descriptions[kernel_name] = f"Installierter Kernel: {kernel_version}"

# GUI erstellen
root = tk.Tk()
root.title("Kernel Installer")
root.geometry("600x500")

tk.Label(root, text="Kernel Version:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

kernel_var = tk.StringVar()
kernel_var.trace("w", update_description)
for idx, (kernel_name, kernel_value) in enumerate(kernel_versions):
    tk.Radiobutton(root, text=kernel_name, variable=kernel_var, value=kernel_value).grid(row=idx+1, column=0, padx=10, sticky=tk.W)

description_label = tk.Label(root, text="", wraplength=300, justify=tk.LEFT)
description_label.grid(row=0, column=1, rowspan=len(kernel_versions)+1, padx=10, pady=5, sticky=tk.NW)

install_button = tk.Button(root, text="Installieren", command=on_install_button_click)
install_button.grid(row=len(kernel_versions)+1, column=0, columnspan=2, pady=20)

# Logo hinzufügen
logo_url = "https://downloads.guideos.de/GuideOS%20-%20Finale%20Logo%20schriftzug%20blau.png"
response = requests.get(logo_url)
logo_image = Image.open(BytesIO(response.content))
logo_image = logo_image.resize((300, 100), Image.ANTIALIAS)
logo_photo = ImageTk.PhotoImage(logo_image)

logo_label = tk.Label(root, image=logo_photo)
logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
logo_label.grid(row=len(kernel_versions)+2, column=0, columnspan=2, pady=20)

root.mainloop()