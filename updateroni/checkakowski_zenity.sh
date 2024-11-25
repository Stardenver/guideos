#!/bin/bash

# Aktualisiere die Paketliste
sudo apt update > /dev/null 2>&1

# Überprüfe auf verfügbare Upgrades
updates=$(apt list --upgradable 2>/dev/null | grep -v "Listing..." | wc -l)

# Wenn es Updates gibt, zeige ein Dialogfenster an
if [ "$updates" -gt 0 ]; then
  zenity --question \
    --title="Updates verfügbar" \
    --text="Es gibt $updates Updates für GuideOS. Möchten Sie diese jetzt installieren?" \
    --ok-label="Installieren" \
    --cancel-label="Abbrechen"
  # Überprüfe den Rückgabewert von zenity
  if [ $? -eq 0 ]; then
    # Benutzer hat "Installieren" geklickt
    sudo apt upgrade -y
  fi
fi
