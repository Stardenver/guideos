#!/bin/bash

# Datei zur Speicherung der UUID
UUID_FILE="$HOME/.installation_uuid"

# API-Endpunkt
URL="https://counter.guideos.de/counter.php"

# Prüfen, ob die UUID-Datei existiert
if [ ! -f "$UUID_FILE" ]; then
  # UUID generieren und speichern
  UUID=$(uuidgen)
  echo "$UUID" > "$UUID_FILE"
else
  # UUID aus der Datei laden
  UUID=$(cat "$UUID_FILE")
fi

# Zähler per POST-Request erhöhen und UUID senden
response=$(curl -X POST -s -w "%{http_code}" -o /dev/null -d "uuid=$UUID" "$URL")

# Überprüfen, ob die Anfrage erfolgreich war (HTTP-Statuscode 200)
if [ "$response" -eq 200 ]; then
    echo "Der Zähler wurde erfolgreich erhöht."
else
    echo "Fehler beim Erhöhen des Zählers. HTTP-Statuscode: $response"
fi
