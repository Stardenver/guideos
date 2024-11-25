#!/bin/bash

# Aktualisiere die Paketliste
sudo apt update > /dev/null 2>&1

# Überprüfe auf verfügbare Upgrades
updates=$(apt list --upgradable 2>/dev/null | grep -v "Listing..." | wc -l)

# Wenn es Updates gibt, sende eine Benachrichtigung
if [ "$updates" -gt 0 ]; then
  notify-send "Updates verfügbar" "Es gibt $updates Updates für GuideOS. Bitte installieren Sie diese bei Gelegenheit mit 'sudo apt upgrade'."
fi
