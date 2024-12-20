<?php
// Datei, die den Zähler speichert
$file = 'counter.txt';

// Initialisiere die Datei, falls sie nicht existiert
if (!file_exists($file)) {
    file_put_contents($file, 0);
}

// Aktuellen Zählerstand laden
$count = (int)file_get_contents($file);

// Prüfen, ob der Zähler hochgezählt werden soll
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Zähler um 1 erhöhen
    $count++;
    file_put_contents($file, $count);
}

// Zähler als JSON zurückgeben
header('Content-Type: application/json');
echo json_encode(['count' => $count]);
?>