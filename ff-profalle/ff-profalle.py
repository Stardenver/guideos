#!/usr/bin/env python3

import os
import shutil
from tkinter import Tk, Label, Listbox, Entry, Button, StringVar, END, messagebox
from cryptography.fernet import Fernet

def get_firefox_profiles():
    profile_path = os.path.expanduser("~/.mozilla/firefox")
    profiles = [d for d in os.listdir(profile_path) if os.path.isdir(os.path.join(profile_path, d))]
    return profiles

def backup_and_encrypt_profile(profile, password):
    profile_path = os.path.expanduser(f"~/.mozilla/firefox/{profile}")
    backup_path = os.path.expanduser(f"~/backup_{profile}.zip")
    shutil.make_archive(f"~/backup_{profile}", 'zip', profile_path)
    
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    
    with open(backup_path, 'rb') as file:
        file_data = file.read()
    
    encrypted_data = cipher_suite.encrypt(file_data)
    
    with open(backup_path, 'wb') as file:
        file.write(encrypted_data)
    
    with open(os.path.expanduser(f"~/backup_{profile}_key.key"), 'wb') as key_file:
        key_file.write(key)

def on_backup():
    selected_profile = profile_listbox.get(profile_listbox.curselection())
    password = password_var.get()
    
    if selected_profile and password:
        backup_and_encrypt_profile(selected_profile, password)
        messagebox.showinfo("Success", "Backup and encryption completed successfully.")
    else:
        messagebox.showerror("Error", "Please select a profile and enter a password.")

app = Tk()
app.title("Firefox Profile Backup")

Label(app, text="Select Firefox Profile:").pack()

profile_listbox = Listbox(app)
profiles = get_firefox_profiles()
for profile in profiles:
    profile_listbox.insert(END, profile)
profile_listbox.pack()

Label(app, text="Enter Password:").pack()

password_var = StringVar()
Entry(app, textvariable=password_var, show='*').pack()

Button(app, text="Backup and Encrypt", command=on_backup).pack()

app.mainloop()
