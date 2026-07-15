# JSON-LD Meta Field

Dieses Typemill-Plugin ergänzt im bestehenden Meta-Tab des Markdown-Editors ein Feld `JSON-LD`.

Der Feldwert wird von Typemill in der jeweiligen Seiten-YAML unter folgendem Pfad gespeichert:

```yaml
meta:
  json_ld: |-
    {
      "@context": "https://schema.org"
    }
```

## Installation

1. Den Ordner `plugins/jsonldmeta/` vollständig in das Typemill-Verzeichnis `plugins/jsonldmeta/` auf dem Webspace kopieren.
2. Im Typemill-Backend unter `Plugins` das Plugin `JSON-LD Meta Field` aktivieren.
3. Eine Seite im Markdown-Editor öffnen und den Bereich `Meta` aufrufen.
4. Vorhandenes JSON-LD prüfen und erst danach speichern.

Das Feld erwartet nur den JSON-Inhalt. Ein umschließendes `<script type="application/ld+json">` gehört nicht in das Eingabefeld.
