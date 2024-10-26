import requests
import subprocess
import base64
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView

# Basis-URL und API-Schlüssel
base_url = "https://bugs.guideos.de"
api_key = "88ccd4679adefb372625dfce01b61cef52053558"  # Hier den API-Schlüssel einfügen

# Funktion zum Abrufen von inxi-Systeminformationen
def get_inxi_info():
    try:
        result = subprocess.run(["inxi", "-F", "-c", "0"], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return "Fehler: 'inxi' konnte nicht ausgeführt werden."

# Funktion zum Erstellen eines Tickets
def create_ticket(subject, description, attachment_path=None):
    if not subject or not description.strip():
        show_popup("Eingabefehler", "Bitte Betreff und Beschreibung ausfüllen.")
        return False

    # inxi-Informationen zur Beschreibung hinzufügen
    system_info = get_inxi_info()
    full_description = f"{description}\n\nSysteminformationen:\n{system_info}"

    issue_data = {
        "issue": {
            "project_id": "guideos",
            "subject": subject,
            "description": full_description,
            "tracker_id": 1,
            "status_id": 1,
            "priority_id": 2,
        }
    }

    url = f"{base_url}/issues.json"
    headers = {
        "X-Redmine-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(url, json=issue_data, headers=headers)
        response.raise_for_status()

        if response.status_code == 201:
            ticket_id = response.json().get("issue", {}).get("id", "unbekannt")
            success_message = f"Ticket erfolgreich erstellt. Ticket-ID: {ticket_id}"

            # Wenn eine Datei als Anhang ausgewählt wurde, lade sie hoch
            if attachment_path:
                upload_attachment(ticket_id, attachment_path)
                success_message += f"\nAnhang {attachment_path} erfolgreich hinzugefügt."

            show_popup("Erfolg", success_message)
            return True
        else:
            show_popup("Fehler", f"Fehler beim Erstellen des Tickets. Statuscode: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        show_popup("Anfragefehler", f"Fehler bei der API-Anfrage: {e}")
        return False

# Funktion zum Hochladen eines Anhangs mit Debugging
def upload_attachment(ticket_id, file_path):
    with open(file_path, "rb") as file:
        # Dateiinhalt als Binärdaten lesen
        file_content = file.read()

    url = f"{base_url}/uploads.json"
    headers = {
        "X-Redmine-API-Key": api_key,
        "Content-Type": "application/octet-stream",
        "Accept": "application/json"
    }

    # Datei als Binärdaten senden, um Token zu erhalten
    response = requests.post(url, headers=headers, data=file_content)

    # Debugging-Ausgabe für den Upload-Prozess
    print("Upload Status Code:", response.status_code)
    print("Upload Response Text:", response.text)

    response.raise_for_status()

    # Den Token vom Upload abholen
    upload_token = response.json().get("upload", {}).get("token")

    # Zweiter API-Aufruf, um den Anhang dem Ticket hinzuzufügen
    issue_update_url = f"{base_url}/issues/{ticket_id}.json"
    issue_data = {
        "issue": {
            "uploads": [
                {
                    "token": upload_token,
                    "filename": file_path.split("/")[-1],
                    "description": "Screenshot oder Anhang"
                }
            ]
        }
    }
    headers["Content-Type"] = "application/json"  # JSON für den zweiten Aufruf

    response = requests.put(issue_update_url, json=issue_data, headers=headers)

    # Debugging-Ausgabe für den Anhang-Update-Prozess
    print("Attachment Update Status Code:", response.status_code)
    print("Attachment Update Response Text:", response.text)

    response.raise_for_status()
    return response

# Popup-Anzeige
def show_popup(title, message):
    popup_layout = BoxLayout(orientation="vertical", padding=10)
    popup_label = Label(text=message)
    close_button = Button(text="Schließen", size_hint=(1, 0.2))
    popup_layout.add_widget(popup_label)
    popup_layout.add_widget(close_button)

    popup = Popup(title=title, content=popup_layout, size_hint=(0.75, 0.5))
    close_button.bind(on_release=popup.dismiss)
    popup.open()

# Funktion zur Dateiauswahl
def open_filechooser(instance, parent):
    filechooser_layout = BoxLayout(orientation="vertical", padding=10)
    filechooser = FileChooserListView(size_hint=(1, 0.8))
    select_button = Button(text="Datei auswählen", size_hint=(1, 0.2))

    def select_file(instance):
        parent.selected_file = filechooser.selection[0] if filechooser.selection else None
        parent.file_label.text = f"Ausgewählte Datei: {parent.selected_file.split('/')[-1]}" if parent.selected_file else "Keine Datei ausgewählt"
        popup.dismiss()

    select_button.bind(on_release=select_file)
    filechooser_layout.add_widget(filechooser)
    filechooser_layout.add_widget(select_button)

    popup = Popup(title="Datei auswählen", content=filechooser_layout, size_hint=(0.75, 0.75))
    popup.open()

# Kivy App Klasse
class RedmineTicketApp(App):
    def build(self):
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Betreff-Feld
        self.layout.add_widget(Label(text="Betreff:"))
        self.subject_input = TextInput(multiline=False)
        self.layout.add_widget(self.subject_input)

        # Fehlerbeschreibung
        self.layout.add_widget(Label(text="Fehlerbeschreibung:"))
        self.description_input = TextInput(multiline=True)
        self.layout.add_widget(self.description_input)

        # Anhang
        self.file_label = Label(text="Keine Datei ausgewählt")
        self.layout.add_widget(self.file_label)
        file_button = Button(text="Anhang auswählen", size_hint=(1, 0.2))
        file_button.bind(on_release=lambda instance: open_filechooser(instance, self))
        self.layout.add_widget(file_button)

        # Erstellen-Button
        submit_button = Button(text="Ticket erstellen", size_hint=(1, 0.2))
        submit_button.bind(on_release=self.on_submit)
        self.layout.add_widget(submit_button)

        self.selected_file = None  # Variable für den Dateipfad
        return self.layout

    def on_submit(self, instance):
        subject = self.subject_input.text
        description = self.description_input.text
        # Wenn Ticket erfolgreich erstellt wird, schließe die App
        if create_ticket(subject, description, self.selected_file):
            self.stop()

# App starten
if __name__ == "__main__":
    RedmineTicketApp().run()
