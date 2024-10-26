#!/bin/bash

# Define the package name and version
PACKAGE_NAME="stat-denver-tools"
VERSION="0.01"

# Define the dependencies
DEPENDENCIES="yad"

# Create the folder structure
mkdir -p ~/stat-denver-tools/debian/DEBIAN
mkdir -p ~/stat-denver-tools/debian/usr/bin
mkdir -p ~/stat-denver-tools/debian/usr/share/doc/$PACKAGE_NAME
mkdir -p ~/stat-denver-tools/debian/usr/share/applications

# Copy files to correct locations
cp stat-denver-tools ~/stat-denver-tools/debian/usr/bin/
cp LICENSE ~/stat-denver-tools/debian/usr/share/doc/$PACKAGE_NAME/LICENSE

# Create the desktop entry file
cat > ~/stat-denver-tools/debian/usr/share/applications/stat-denver-tools.desktop << EOF
[Desktop Entry]
Version=2.1
Exec=stat-denver-tools
Name=StatDenverTools
GenericName=StatD
Encoding=UTF-8
Terminal=false
StartupWMClass=StatD
Type=Application
Categories=System
Icon=help
EOF

# Create the copyright file
cat > ~/stat-denver-tools/debian/usr/share/doc/$PACKAGE_NAME/copyright << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: PiGro - Just Click It!
Source: https://github.com/actionschnitzel/PiGro-JCI

Files: *
Copyright: 2024 Boris Schäfer
License: GPL-3
 This package is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, version 3.
 .
 This package is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 .
 You should have received a copy of the GNU General Public License
 along with this program. If not, see <https://www.gnu.org/licenses/>
 .
 On Debian systems, the complete text of the GNU General
 Public License version 3 can be found in "/usr/share/common-licenses/GPL-3".
EOF

# Create the control file
cat > ~/stat-denver-tools/debian/DEBIAN/control << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Architecture: all
Maintainer: Timo Westphal <pigroxtrmo@gmail.com>
Depends: yad, curl, inxi
Section: misc
Priority: optional
Homepage: https://zestful-pigroxtrmo.wordpress.com/
License: GPL-3.0
Description: A system control tool for Raspberry Pi
 PiGro is a system configuration tool inspired by openSUSE's YaST
 but designed with the user-friendliness of Linux Mint in mind.
 It equips Raspberry Pi OS with graphical interfaces for tasks 
 that would otherwise require the terminal.
 PiGro is also optimized for Ubuntu, Ubuntu Mate, and MX Linux.
EOF

# Set permissions and ownership
chmod 755 ~/stat-denver-tools/debian/usr/bin/stat-denver-tools
chmod 644 ~/stat-denver-tools/debian/usr/share/applications/stat-denver-tools.desktop
chmod -R 755 ~/stat-denver-tools/debian/usr/share/doc/$PACKAGE_NAME

# Build the package
dpkg-deb --build ~/stat-denver-tools/debian

# Move the package to the current directory
mv ~/stat-denver-tools/debian.deb ~/stat-denver-tools/$PACKAGE_NAME-$VERSION.deb

# Clean up the temporary files
#sudo rm -rf ~/stat-denver-tools/debian
