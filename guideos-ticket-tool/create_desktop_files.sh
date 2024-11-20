#!/bin/bash

# Sicherstellen, dass die Verzeichnisse existieren
mkdir -p debian/guideos-ticket-tool/usr/share/applications
#mkdir -p debian/guideos-ticket-tool/etc/xdg/autostart

# Erstellen der ersten .desktop-Datei
cat > debian/guideos-ticket-tool/usr/share/applications/guideos-ticket-tool.desktop <<EOL
[Desktop Entry]
Version=2.1
Exec=guideos-ticket-tool
Name=GuideOS Ticket Tool
GenericName=Ticket Tool
Encoding=UTF-8
Terminal=false
StartupWMClass=Ticket Tool
Type=Application
Categories=System
Icon=guideos-ticket-tool-logo
Path=/opt/guideos-ticket-tool/
EOL