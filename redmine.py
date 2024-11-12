import os
import requests
import subprocess  # Dieses Modul importieren
import tkinter as tk
from tkinter import filedialog, messagebox


# API-Token aus der Umgebungsvariable laden
api_token = os.getenv('REDMINE_API_TOKEN')

if not api_token:
    raise ValueError("API-Token nicht gefunden. Bitte stelle sicher, dass die Umgebungsvariable REDMINE_API_TOKEN gesetzt ist.")

# Redmine-URL und Projekt-Identifier
redmine_url = 'https://bugs.guideos.de'
project_identifier = 'guideos'  # Dein Projekt-Identifier

# Funktion zum Senden der Daten an Redmine
def ticket_erstellen():
    betreff = betreff_entry.get()
    beschreibung = beschreibung_text.get("1.0", tk.END)
    screenshot_path = screenshot_entry.get()

    if not betreff.strip() or not beschreibung.strip():
        messagebox.showerror("Fehler", "Betreff und Beschreibung dürfen nicht leer sein.")
        return

    # inxi-Informationen zur Beschreibung hinzufügen
    system_info = get_inxi_info()
    full_description = f"{beschreibung}\n\nSysteminformationen:\n{system_info}"

    headers = {
        'X-Redmine-API-Key': api_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Ticket-Payload
    payload = {
        'issue': {
            'project_id': project_identifier,
            'subject': betreff,
            'description': full_description,
        }
    }

    try:
        response = requests.post(f'{redmine_url}/issues.json', json=payload, headers=headers)
        response.raise_for_status()

        if response.status_code == 201:
            ticket_id = response.json().get("issue", {}).get("id", "unbekannt")
            success_message = f"Ticket erfolgreich erstellt. Ticket-ID: {ticket_id}"

            # Wenn eine Datei als Anhang ausgewählt wurde, lade sie hoch
            if screenshot_path:
                upload_response = upload_attachment(ticket_id, screenshot_path)
                if upload_response:
                    success_message += f"\nAnhang {screenshot_path} erfolgreich hinzugefügt."

            show_popup("Erfolg", success_message)
            return True
        else:
            show_popup("Fehler", f"Fehler beim Erstellen des Tickets. Statuscode: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        show_popup("Anfragefehler", f"Fehler bei der API-Anfrage: {e}")
        return False

# Funktion zum Hochladen eines Anhangs
def upload_attachment(ticket_id, file_path):
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()

        url = f"{redmine_url}/uploads.json"
        headers = {
            "X-Redmine-API-Key": api_token,
            "Content-Type": "application/octet-stream",
            "Accept": "application/json"
        }

        response = requests.post(url, headers=headers, data=file_content)

        # Debugging-Ausgabe
        print("Upload Status Code:", response.status_code)
        print("Upload Response Text:", response.text)

        response.raise_for_status()

        # Den Token vom Upload abholen
        upload_token = response.json().get("upload", {}).get("token")

        # Anhang dem Ticket hinzufügen
        issue_update_url = f"{redmine_url}/issues/{ticket_id}.json"
        issue_data = {
            "issue": {
                "uploads": [
                    {
                        "token": upload_token,
                        "filename": os.path.basename(file_path),
                        "description": "Screenshot oder Anhang"
                    }
                ]
            }
        }
        headers["Content-Type"] = "application/json"
        response = requests.put(issue_update_url, json=issue_data, headers=headers)

        # Debugging-Ausgabe
        print("Attachment Update Status Code:", response.status_code)
        print("Attachment Update Response Text:", response.text)

        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        show_popup("Fehler", f"Fehler beim Hochladen des Anhangs: {e}")
        return False

# Funktion zur Anzeige von Systeminformationen
def get_inxi_info():
    try:
        result = subprocess.run(["inxi", "-F", "-c", "0"], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return "Fehler: 'inxi' konnte nicht ausgeführt werden."

# Popup-Anzeige
def show_popup(title, message):
    messagebox.showinfo(title, message)

# Funktion zur Auswahl einer Screenshot-Datei
def screenshot_waehlen():
    file_path = filedialog.askopenfilename(
        title="Wähle einen Screenshot aus",
        filetypes=[("Alle Dateien", "*.*"), ("Bilddateien", "*.png;*.jpg;*.jpeg;*.gif")]
    )
    if file_path:
        screenshot_entry.delete(0, tk.END)
        screenshot_entry.insert(0, file_path)

# GUI erstellen
root = tk.Tk()
root.title("GuideOS Bug melden")

tk.Label(root, text="Betreff:").pack(pady=5)
betreff_entry = tk.Entry(root, width=50)
betreff_entry.pack(pady=5)

tk.Label(root, text="Fehlerbeschreibung:").pack(pady=5)
beschreibung_text = tk.Text(root, height=10, width=50)
beschreibung_text.pack(pady=5)

tk.Label(root, text="Screenshot (optional):").pack(pady=5)
screenshot_frame = tk.Frame(root)
screenshot_frame.pack(pady=5)
screenshot_entry = tk.Entry(screenshot_frame, width=40)
screenshot_entry.pack(side=tk.LEFT, padx=5)
screenshot_button = tk.Button(screenshot_frame, text="Durchsuchen", command=screenshot_waehlen)
screenshot_button.pack(side=tk.LEFT)

submit_button = tk.Button(root, text="Ticket erstellen", command=ticket_erstellen)
submit_button.pack(pady=10)

root.mainloop()

