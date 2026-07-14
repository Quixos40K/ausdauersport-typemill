# Ausdauersport × Typemill

Dieses Repository ist der versionierte Master-Stand für die Inhalte und das angepasste Theme der Website von Oliver Nix.

Das Projekt verbindet drei Ebenen:

- ein strukturiertes Wissenssystem zu Ausdauersport, Trainingswissenschaft, Leistungsphysiologie, Biomechanik, Ernährung und Regeneration,
- eine technische Umsetzung mit Typemill als Flat-File-CMS,
- einen praktischen Proof of Concept für SEO, AEO, GEO, LLM-Lesbarkeit, strukturierte Daten und komplexe Content-Systeme.

## Verbindlicher Stand

Der Branch `main` ist der produktive Master-Stand.

Frühere Repository-Versionen, alte ZIP-Exporte und verworfene Zwischenstände sind nicht mehr verbindlich. Die fachlichen Projektquellen, Arbeitsanweisungen und konzeptionellen Grundlagen bleiben gültig, sofern sie dem aktuellen Repository nicht widersprechen.

## Repository-Struktur

```text
content/          Typemill-Inhalte als Markdown- und YAML-Dateipaare
themes/           versionierter Theme-Code
README.md         Projekt- und Workflow-Dokumentation
.gitignore        Ausschlüsse für lokale Dateien, Laufzeitdaten und Secrets
```

Typemill verwendet für Inhalte Dateipaare:

```text
Detailseite:       seitenname.md + seitenname.yaml
Containerseite:    index.md + index.yaml
```

Markdown enthält den sichtbaren Inhalt. YAML enthält Typemill-Metadaten und derzeit auch seitenspezifische strukturierte Daten.

## Zielarchitektur

```text
GitHub
  ↓
Prüfung und Versionierung
  ↓
Deployment
  ↓
Typemill auf dem Webspace
  ↓
HTML, Metadaten und JSON-LD
```

GitHub ist die zentrale Arbeits- und Prüfquelle. Typemill bleibt das Live-CMS und rendert die Website aus den versionierten Dateien.

## Arbeitsregeln

1. Änderungen werden nicht direkt per FTP in den produktiven Content geschrieben.
2. Neue Inhalte und Theme-Anpassungen werden zuerst im Repository gepflegt.
3. `main` enthält nur freigegebene, produktive Änderungen.
4. Secrets, Benutzerdateien, Cache und Typemill-Laufzeitdaten gehören nicht in dieses Repository.
5. Markdown, YAML, interne Links, strukturierte Daten und Quellen sollen künftig automatisiert geprüft werden.
6. Fachliche Quellen werden nicht ohne inhaltliche Prüfung entfernt oder ersetzt.

## Aktueller Umfang

Im Repository enthalten sind:

- die vollständige aktuelle Content-Struktur,
- Markdown-Artikel und Containerseiten,
- zugehörige Typemill-YAML-Dateien,
- Quellenblöcke, FAQ-Bereiche und Mermaid-Diagramme,
- das verwendete Guide-Theme einschließlich Anpassungen.

Noch nicht vollständig als reproduzierbarer Prozess umgesetzt sind:

- automatische Qualitätsprüfungen mit GitHub Actions,
- ein dokumentierter Deployment-Prozess,
- die vollständige Medienstrategie,
- eine zentrale und automatisierte Erzeugung bzw. Validierung von JSON-LD.

## Positionierung des Projekts

Der Ausdauersport-Bereich ist kein klassischer Trainingsblog. Er ist ein strukturiertes Wissenssystem, an dem die Verbindung aus fachlicher Recherche, semantischer Architektur, SEO, AEO, GEO und LLM-orientierter Content-Modellierung praktisch demonstriert wird.

Die sportwissenschaftlichen Inhalte dienen der allgemeinen Information und Einordnung. Sie ersetzen keine medizinische Diagnose, Behandlung oder individuelle Trainingsberatung.

## Nächste technische Schritte

1. Repository-Grundlage abschließen.
2. Theme-Ausgabe für JSON-LD prüfen und absichern.
3. Validierung für Markdown, YAML und strukturierte Daten einführen.
4. Medien- und Deployment-Strategie dokumentieren.
5. Branch- und Release-Workflow festlegen.
