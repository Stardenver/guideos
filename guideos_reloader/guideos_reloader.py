#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import uuid
import boto3
import qrcode
import subprocess
from PIL import Image, ImageTk

# Minio-Konfiguration
MINIO_URL = 'https://minio-api.guideos.net'
ACCESS_KEY = 'hEX5rTBj9ELq3pT9n8oy'
SECRET_KEY = 'rGK01FLIeF7Vln1XrOJxR3cbaDLcsOqxwnHaNjch'
BUCKET_NAME = 'guideosreloader'

# Programme aus JSON laden
with open('programme.json', 'r') as file:
    daten = json.load(file)['programme']

def upload_config(datei, dateiname):
    s3_client = boto3.client(
        's3',
        endpoint_url=MINIO_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    try:
        s3_client.upload_file(datei, BUCKET_NAME, dateiname, ExtraArgs={"ContentType": "application/json"})
        return True
    except Exception as e:
        messagebox.showerror("Fehler", f"Upload fehlgeschlagen: {e}")
        return False

def download_config(uuid):
    s3_client = boto3.client(
        's3',
        endpoint_url=MINIO_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    dateiname = f"{uuid}.json"
    try:
        s3_client.download_file(BUCKET_NAME, dateiname, dateiname)
        return dateiname
    except Exception as e:
        messagebox.showerror("Fehler", f"Download fehlgeschlagen: {e}")
        return None

def start_window():
    root = tk.Tk()
    root.title('GuideOS-Reloader')
    root.geometry('400x250')

    ttk.Label(root, text='Wähle eine Option:', font=('Arial', 14)).pack(pady=20)
    ttk.Button(root, text='Konfiguration sichern', command=auswahl_window).pack(pady=10)
    ttk.Button(root, text='Konfiguration wiederherstellen', command=wiederherstellung_window).pack(pady=10)
    ttk.Button(root, text='Beenden', command=root.quit).pack(pady=10)
    return root

def auswahl_window():
    window = tk.Toplevel(root)
    window.title('Programme auswählen')
    window.geometry('800x600')

    ttk.Label(window, text='Programme auswählen:', font=('Arial', 14)).pack(pady=10)
    
    canvas = tk.Canvas(window)
    scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    global vars
    vars = []
    for programm in daten:
        var = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text=f"{programm['name']} – {programm['beschreibung']}", variable=var).pack(anchor='w', padx=10, pady=2)
        vars.append((var, programm['name']))
    
    ttk.Button(window, text='Auswahl speichern und hochladen', command=speichere_auswahl).pack(pady=10)
    ttk.Button(window, text='Zurück', command=window.destroy).pack(pady=5)

def speichere_auswahl():
    ausgewaehlt = [name for var, name in vars if var.get()]
    if not ausgewaehlt:
        messagebox.showwarning('Warnung', 'Bitte mindestens ein Programm auswählen.')
        return
    
    config = {"ausgewaehlte_programme": ausgewaehlt}
    dateiname = f'{uuid.uuid4()}.json'
    with open(dateiname, 'w') as file:
        json.dump(config, file, indent=4)
    
    if upload_config(dateiname, dateiname):
        zeige_uuid(dateiname[:-5])
    else:
        messagebox.showerror('Fehler', 'Upload fehlgeschlagen.')

def wiederherstellung_window():
    window = tk.Toplevel(root)
    window.title("Konfiguration wiederherstellen")
    window.geometry("400x300")
    
    ttk.Label(window, text="Gib die UUID ein oder wähle eine Datei:", font=("Arial", 12)).pack(pady=5)
    uuid_entry = ttk.Entry(window, font=("Arial", 12))
    uuid_entry.pack(fill='x', padx=10, pady=5)
    
    def wähle_datei():
        datei = filedialog.askopenfilename(filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")])
        if datei:
            uuid_entry.delete(0, tk.END)
            uuid_entry.insert(0, datei)
    
    def starte_wiederherstellung():
        uuid_text = uuid_entry.get().strip()
        if not uuid_text:
            messagebox.showwarning("Fehler", "Bitte eine gültige UUID oder Datei eingeben.")
            return
        messagebox.showinfo("Info", f"Wiederherstellung gestartet für UUID/Datei: {uuid_text}")
    
    ttk.Button(window, text="Datei auswählen", command=wähle_datei).pack(pady=5)
    ttk.Button(window, text="Wiederherstellen", command=starte_wiederherstellung).pack(pady=10)
    ttk.Button(window, text="Zurück", command=window.destroy).pack(pady=5)

# GUI starten
root = start_window()
root.mainloop()