#!/usr/bin/python3

import os
import requests
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

# API-Token aus der Umgebungsvariable laden
api_token = os.getenv("MANTIS_API_TOKEN", "o-7QYYx6xmK9F_6YTyIwjnPryZawcey3")

if not api_token:
    raise ValueError(
        "API-Token nicht gefunden. Bitte stelle sicher, dass die Umgebungsvariable MANTIS_API_TOKEN gesetzt ist."
    )

# Mantis-URL und Projekt-Identifier
mantis_url = "https://mantis.guideos.net"
project_name = "guideos"  # Dein Projektname
project_id = 1  # Deine Projekt-ID

# Funktion zum Senden der Daten an Mantis
def ticket_erstellen():
    betreff = betreff_entry.get()
    beschreibung = beschreibung_text.get("1.0", tk.END)
    screenshot_path = screenshot_entry.get()

    if not betreff.strip() or not beschreibung.strip():
        messagebox.showerror(
            "Fehler", "Betreff und Beschreibung dürfen nicht leer sein."
        )
        return

    # inxi-Informationen zur Beschreibung hinzufügen
    system_info = get_inxi_info()
    full_description = f"{beschreibung}\n\nSysteminformationen:\n{system_info}"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Ticket-Payload
    payload = {
        "summary": betreff,
        "description": full_description,
        "project": {"id": project_id, "name": project_name},
    }

    response = requests.post(f"{mantis_url}/api/rest/issues/", json=payload, headers=headers)

    if response.status_code == 201:
        messagebox.showinfo("Erfolg", "Ticket wurde erfolgreich erstellt.")
    else:
        messagebox.showerror("Fehler", f"Fehler beim Erstellen des Tickets: {response.text}")

# Anhang dem Ticket hinzufügen
def anhang_hinzufuegen(ticket_id, file_path):
    try:
        upload_url = f"{mantis_url}/api/rest/issues/{ticket_id}/files"
        with open(file_path, "rb") as file:
            files = {"file": (os.path.basename(file_path), file)}
            headers = {
                "Authorization": f"Bearer {api_token}",
            }
            response = requests.post(upload_url, files=files, headers=headers)

        # Debugging-Ausgabe
        print("Attachment Upload Status Code:", response.status_code)
        print("Attachment Upload Response Text:", response.text)

        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        show_popup("Fehler", f"Fehler beim Hochladen des Anhangs: {e}")
        return False

# Funktion zur Anzeige von Systeminformationen
def get_inxi_info():
    return "Dummy-Systeminformationen"

# Popup-Anzeige
def show_popup(title, message):
    messagebox.showinfo(title, message)

# Funktion zur Auswahl einer Screenshot-Datei
def screenshot_waehlen():
    file_path = filedialog.askopenfilename(
        title="Wähle einen Screenshot aus",
        filetypes=[
            ("Alle Dateien", "*.*"),
            ("Bilddateien", "*.png;*.jpg;*.jpeg;*.gif"),
        ],
    )
    if file_path:
        screenshot_entry.delete(0, tk.END)
        screenshot_entry.insert(0, file_path)

def open_bug_page():
    webbrowser.open(
        "https://bugs.guideos.net/projects/guideos/issues?set_filter=1&tracker_id=1"
    )

# GUI erstellen
root = tk.Tk()
root.title("GuideOS Bug melden")
# root.geometry= "500x600"
home = os.path.expanduser("~")
script_dir = os.path.dirname(os.path.abspath(__file__))
application_path = os.path.dirname(script_dir)
# Just simply import the azure.tcl file
root.tk.call(
    "source",
    os.path.join(f"{application_path}/guideos-ticket-tool/azure-adwaita-ttk/azure.tcl"),
)  # replace with {application_path} in final.

# Then set the theme you want with the set_theme procedure
# root.tk.call("set_theme", "light")
# or
root.tk.call("set_theme", "light")

titel_frame = ttk.LabelFrame(root, text="Betreff", padding=20)
titel_frame.pack(fill="x", pady=5, padx=20)

betreff_entry = ttk.Entry(titel_frame, width=50)
betreff_entry.pack(pady=5, fill="x")
betreff_entry.insert("end", "Gibt einen Titel ein:")

issue_text_frame = ttk.LabelFrame(root, text="Fehlerbeschreibung", padding=20)
issue_text_frame.pack(fill="x", pady=5, padx=20)

beschreibung_text = tk.Text(
    issue_text_frame, borderwidth=0, highlightthickness=1, height=15
)
beschreibung_text.pack(pady=5, padx=5, fill="x", expand=True)

beschreibung_text.insert("end", "Schreibe einen Text:")

opt_frame = ttk.LabelFrame(root, text="Screenshot (optional)", padding=20)
opt_frame.pack(fill="x", pady=5, padx=20)

screenshot_entry = ttk.Entry(opt_frame)
screenshot_entry.pack(fill="x", expand=True, side=tk.LEFT, padx=5)
screenshot_button = ttk.Button(
    opt_frame, text="Durchsuchen", command=screenshot_waehlen
)
screenshot_button.pack(side=tk.LEFT)

submit_button = ttk.Button(
    root, text="Ticket erstellen", command=ticket_erstellen, style="Accent.TButton"
)
submit_button.pack(pady=20, padx=20, fill="x")

web_button = ttk.Button(root, text="Alle Meldungen einsehen", command=open_bug_page)
web_button.pack(pady=20, padx=20, fill="x")

root.mainloop()
