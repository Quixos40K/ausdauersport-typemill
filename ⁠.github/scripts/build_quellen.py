import os
import glob
import re

# Ordner, in dem deine Typemill-Texte liegen
CONTENT_DIR = "content/00-ausdauersport"
# Die Datei, die der Roboter automatisch erstellen soll
OUTPUT_FILE = os.path.join(CONTENT_DIR, "99-quellenverzeichnis.md")

def extract_sources():
    all_sources = set() # Set filtert automatisch exakte Duplikate heraus
    
    # Suche alle .md Dateien
    md_files = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)
    
    for filepath in md_files:
        # Die Ausgabedatei selbst und den Disclaimer überspringen
        if filepath.endswith("99-quellenverzeichnis.md") or "disclaimer" in filepath.lower():
            continue
            
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Suche nach dem Wort "Quellen" als Überschrift
        if '## Quellen' in content:
            # Schneide alles ab "## Quellen" ab
            quellen_block = content.split('## Quellen')[1]
            
            # Schneide den Disclaimer am Ende weg, falls vorhanden
            if 'Hinweis: Dieser Artikel' in quellen_block:
                quellen_block = quellen_block.split('Hinweis: Dieser Artikel')[0]
                
            # Teile den Block in einzelne Zeilen/Absätze und filtere leere Zeilen
            lines = quellen_block.split('\n')
            current_source = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("Quelle") or line.startswith("### Quelle") or line.startswith("["):
                    # Wenn eine neue Quelle anfängt und wir schon eine gesammelt haben, speichern
                    if current_source and "http" in current_source:
                        all_sources.add(current_source.strip())
                    current_source = line
                elif line:
                    # Füge Text zur aktuellen Quelle hinzu
                    current_source += " " + line
            
            # Die letzte Quelle der Datei noch hinzufügen
            if current_source and "http" in current_source:
                all_sources.add(current_source.strip())

    return all_sources

def write_master_file(sources):
    # Sortiere die Quellen alphabetisch
    sorted_sources = sorted(list(sources))
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Wissenschaftliches Quellenverzeichnis\n\n")
        f.write("Dieses Lexikon basiert auf der aktuellen sportmedizinischen, physiologischen und biomechanischen Primärliteratur. ")
        f.write("Die folgende Liste wird automatisch aus allen Artikeln dieses Projekts generiert und laufend aktualisiert.\n\n")
        f.write("---\n\n")
        
        for source in sorted_sources:
            # Bereinige die Formatierung ein wenig für eine schöne Liste
            clean_source = re.sub(r'^###\s*Quelle\s*\d*:\s*', '', source)
            clean_source = re.sub(r'^Quelle\s*\d*:\s*', '', clean_source)
            f.write(f"* {clean_source}\n\n")

if __name__ == "__main__":
    print("Starte Quellen-Extraktion...")
    extracted = extract_sources()
    write_master_file(extracted)
    print(f"Erfolgreich {len(extracted)} Quellen extrahiert und in {OUTPUT_FILE} gespeichert.")
