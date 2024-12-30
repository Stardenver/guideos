<?php
// Datei, die den Zähler speichert
$file = 'counter.txt';

// Initialisiere die Datei, falls sie nicht existiert
if (!file_exists($file)) {
    file_put_contents($file, 0);
}

// Datei zur Speicherung der UUIDs
$uuid_file = 'uuids.txt';

// Initialisiere die Datei, falls sie nicht existiert
if (!file_exists($uuid_file)) {
    file_put_contents($uuid_file, '');
}

// Aktuellen Zählerstand laden
$count = (int)file_get_contents($file);

// Aktuelle UUIDs laden
$uuids = file($uuid_file, FILE_IGNORE_NEW_LINES);

// Prüfen, ob eine UUID gesendet wurde
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['uuid'])) {
    $uuid = $_POST['uuid'];

    // Prüfen, ob die UUID bereits bekannt ist
    if (!in_array($uuid, $uuids)) {
        // UUID hinzufügen und speichern
        $uuids[] = $uuid;
        file_put_contents($uuid_file, implode(PHP_EOL, $uuids) . PHP_EOL);

        // Zähler um 1 erhöhen
        $count++;
        file_put_contents($file, $count);
    }
}

// Zähler als JSON zurückgeben
header('Content-Type: application/json');
echo json_encode(['count' => $count]);
?>
