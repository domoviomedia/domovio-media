<?php
// Nimmt das Anfrageformular entgegen und schickt es per Mail. Speichert nichts.
const EMPFAENGER = 'info@domoviomedia.de';
const ABSENDER = 'website@domoviomedia.de';

function weiter(string $ziel): void {
    header('Location: ' . $ziel, true, 303);
    exit;
}
function feld(string $name, int $max = 200): string {
    $wert = trim((string)($_POST[$name] ?? ''));
    return mb_substr(str_replace(["\r", "\n"], ' ', $wert), 0, $max);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    weiter('/kontakt/');
}
// Falle für Bots: Das Feld ist unsichtbar, Menschen lassen es leer.
if (!empty($_POST['website'])) {
    weiter('/danke/');
}

$name = feld('name');
$email = feld('email');
$nachricht = trim(mb_substr((string)($_POST['nachricht'] ?? ''), 0, 5000));
if ($name === '' || $nachricht === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    weiter('/kontakt/?fehler=1#formular');
}

$text = "Neue Anfrage über domoviomedia.de\n\n"
    . "Name: $name\n"
    . 'Firma: ' . feld('firma') . "\n"
    . "E-Mail: $email\n"
    . 'Telefon: ' . feld('telefon') . "\n"
    . 'Immobilie / Ort: ' . feld('objekt') . "\n"
    . 'Interesse: ' . feld('leistung') . "\n\n"
    . $nachricht . "\n";

$betreff = '=?UTF-8?B?' . base64_encode('Anfrage von ' . $name) . '?=';
$kopf = "From: Domovio Media Website <" . ABSENDER . ">\r\n"
    . "Reply-To: $email\r\n"
    . "Content-Type: text/plain; charset=UTF-8\r\n";

if (mail(EMPFAENGER, $betreff, $text, $kopf, '-f' . ABSENDER)) {
    weiter('/danke/');
}
weiter('/kontakt/?fehler=2#formular');
