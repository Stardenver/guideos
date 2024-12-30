### Erklärung

1. **Bash-Skript**:
    - Das Skript prüft, ob eine Datei zur Speicherung der UUID existiert. Wenn nicht, wird eine UUID generiert und gespeichert.
    - Bei jeder Ausführung wird die gespeicherte UUID an das PHP-Skript gesendet.

2. **PHP-Skript**:
    - Das PHP-Skript empfängt die UUID und prüft, ob sie bereits bekannt ist.
    - Wenn die UUID noch nicht bekannt ist, wird sie gespeichert und der Zähler erhöht.
    - Beim erneuten Senden derselben UUID wird der Zähler nicht erneut erhöht.

Diese Lösung stellt sicher, dass Installationen nur einmal gezählt werden, indem eine eindeutige ID pro Installation verwendet wird.
