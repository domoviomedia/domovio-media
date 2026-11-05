# Propertale

Statische Website für Immobilienfotografie im Rhein-Main-Gebiet. Quellen in `src/`, gebaut mit Python ohne Abhängigkeiten.

```bash
python3 build.py
```

Die Ausgabe liegt in `public/` und wird nicht eingecheckt.

| Was | Wo |
| --- | --- |
| Texte der Seiten | `src/pages/` |
| Preise | `src/preise.json`, Kopie aus der Rechnungs-App ohne Anfahrt |
| Domain, E-Mail, Telefon | oben in `build.py`, dazu `src/kontakt.php`, `src/.htaccess`, `src/robots.txt` |
| Aussehen | `src/assets/css/style.css` |

## Auf Strato hochladen

Der Upload läuft nur von Hand über GitHub Actions: Actions, "Auf Strato hochladen", Run workflow. Standard ist ein Probelauf, der nichts verändert. Zum echten Upload den Haken bei Probelauf entfernen.

Nötige Secrets unter Settings, Secrets and variables, Actions:

| Secret | Inhalt |
| --- | --- |
| `STRATO_SFTP_HOST` | SFTP-Server aus dem Strato-Kundenbereich |
| `STRATO_SFTP_USER` | SFTP-Benutzer |
| `STRATO_SFTP_PASSWORD` | SFTP-Passwort |
| `STRATO_SFTP_PATH` | Eigener Zielordner der Seite, zum Beispiel `/domovio-media` |

Der Upload löscht im Zielordner alles, was nicht zur Seite gehört. Der Ordner darf deshalb nichts anderes enthalten, und die Domain muss bei Strato auf genau diesen Ordner zeigen.

Zugangsdaten gehören nie ins Repo.

## Alter Name Domovio Media

Bis November 2026 hieß die Seite Domovio Media. Repo und lokaler Ordner heißen seit dem 05.11.2026 `propertale-website`. Nur der Webspace-Ordner `/domovio-media` bei Strato trägt noch den alten Namen, Besucher sehen ihn nicht. domoviomedia.de bleibt registriert und leitet per `src/.htaccess` auf propertale.de weiter, damit alte Links funktionieren.
