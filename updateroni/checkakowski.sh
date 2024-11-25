#!/bin/bash

# Aktualisiere die Paketliste
sudo apt update > /dev/null 2>&1

# \u00dcberpr\u00fcfe auf verf\u00fcgbare Upgrades
updates=$(apt list --upgradable 2>/dev/null | grep -v "Listing..." | wc -l)

# Wenn es Updates gibt, sende eine Benachrichtigung
if [ "$updates" -gt 0 ]; then
  notify-send "Updates verf\u00fcgbar" "Es gibt $updates Updates f\u00fcr GuideOS. Bitte starte das Update-Tool."
fi



