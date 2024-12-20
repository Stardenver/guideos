#!/bin/bash

# URL des API-Endpunkts
URL="https://counter.guideos.de/counter.php"

# Zähler per POST-Request erhöhen
curl -X POST -s "$URL" > /dev/null
