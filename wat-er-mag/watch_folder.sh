#!/bin/bash

# Verzeichnis, das überwacht werden soll
WATCH_DIR="/path/to/watch"

# Wasserzeichen-Bild
WATERMARK="/path/to/watermark.png"

# Funktion, um ein Wasserzeichen hinzuzufügen
add_watermark() {
    local image=$1
    composite -gravity southeast -geometry +10+10 "$WATERMARK" "$image" "$image"
}

# Überwache den Ordner und reagiere auf neue Dateien
inotifywait -m -e create --format "%w%f" "$WATCH_DIR" | while read NEWFILE
do
    # Prüfe, ob die neue Datei ein Bild ist (optional: erweitern um mehr Formate)
    if [[ "$NEWFILE" =~ \.(jpg|jpeg|png|gif)$ ]]; then
        echo "Neues Bild gefunden: $NEWFILE"
        add_watermark "$NEWFILE"
        echo "Wasserzeichen hinzugefügt: $NEWFILE"
    fi
done
