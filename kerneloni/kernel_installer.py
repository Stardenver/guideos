import tkinter as tk
from tkinter import messagebox
import subprocess

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
        subprocess.run(['sudo', 'apt-get', 'install', kernel_version], check=True)
        messagebox.showinfo("Erfolg", f"Kernel {kernel_version} wurde erfolgreich installiert.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"Fehler bei der Installation des Kernels: {e}")

def on_install_button_click():
    kernel_version = kernel_var.get()
    if kernel_version:
        install_kernel(kernel_version)
    else:
        messagebox.showwarning("Warnung", "Bitte wählen Sie eine Kernel-Version aus.")

def update_description(*args):
    kernel_version = kernel_var.get()
    description = kernel_descriptions.get(kernel_version, "")
    description_label.config(text=description)

# Liste der verfügbaren Kernel-Versionen und ihre Beschreibungen
kernel_versions = ["linux-image-amd64", "linux-image-rt-amd64", "linux-image-liquorix-amd64"]
kernel_descriptions = {
    "linux-image-amd64": "LTS Kernel: Stabil und langfristig unterstützt.",
    "linux-image-rt-amd64": "Real-Time Kernel: Für Echtzeitanwendungen optimiert.",
    "linux-image-liquorix-amd64": "Liquorix Kernel: Für Desktop- und Multimedia-Anwendungen optimiert."
}

# GUI erstellen
root = tk.Tk()
root.title("Kernel Installer")
root.geometry("600x200")

tk.Label(root, text="Kernel Version:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

kernel_var = tk.StringVar()
kernel_var.trace("w", update_description)
for idx, kernel in enumerate(kernel_versions):
    tk.Radiobutton(root, text=kernel, variable=kernel_var, value=kernel).grid(row=idx+1, column=0, padx=10, sticky=tk.W)

description_label = tk.Label(root, text="", wraplength=300, justify=tk.LEFT)
description_label.grid(row=0, column=1, rowspan=len(kernel_versions)+1, padx=10, pady=5, sticky=tk.NW)

install_button = tk.Button(root, text="Installieren", command=on_install_button_click)
install_button.grid(row=len(kernel_versions)+1, column=0, columnspan=2, pady=20)

root.mainloop()