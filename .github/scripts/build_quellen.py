import os
import glob
import re

# Wir suchen direkt im Ordner "content" und all seinen Unterordnern
CONTENT_DIR = "content"
OUTPUT_FILE = os.path.join(CONTENT_DIR, "99-quellenverzeichnis.md")

def extract_sources():
    all_sources = set()
    
    # Finde alle .md Dateien im content-Ordner (rekursiv)
    md_files = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)
    
    for filepath in md_files:
        # Die Ausgabedatei selbst und den Disclaimer überspringen
        if "99-quellenverzeichnis.md" in filepath or "disclaimer" in filepath.lower() or "externe_quellen" in filepath.lower():
            continue
            
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Suche nach dem Wort "Quellen" als Überschrift
        if '## Quellen' in content:
            quellen_block = content.split('## Quellen')[1]
            
            # Schneide den Disclaimer am Ende weg, falls vorhanden
            if 'Hinweis: Dieser Artikel' in quellen_block:
                quellen_block = quellen_block.split('Hinweis: Dieser Artikel')[0]
                
            lines = quellen_block.split('\n')
            current_source = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("Quelle") or line.startswith("### Quelle") or line.startswith("[") or line.startswith("* **"):
                    if current_source and "http" in current_source:
                        all_sources.add(current_source.strip())
                    current_source = line
                elif line:
                    current_source += " " + line
            
            if current_source and "http" in current_source:
                all_sources.add(current_source.strip())

    return all_sources

def write_master_file(sources):
    sorted_sources = sorted(list(sources))
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Wissenschaftliches Quellenverzeichnis\n\n")
        f.write("Dieses Lexikon basiert auf der aktuellen sportmedizinischen, physiologischen und biomechanischen Primärliteratur. ")
        f.write("Die folgende Liste wird automatisch aus allen Artikeln dieses Projekts generiert und laufend aktualisiert.\n\n")
        f.write("---\n\n")
        
        for source in sorted_sources:
            clean_source = re.sub(r'^###\s*Quelle\s*\d*:\s*', '', source)
            clean_source = re.sub(r'^Quelle\s*\d*:\s*', '', clean_source)
            f.write(f"* {clean_source}\n\n")

if __name__ == "__main__":
    print("Starte Quellen-Extraktion...")
    extracted = extract_sources()
    write_master_file(extracted)
    print(f"Erfolgreich {len(extracted)} Quellen extrahiert und in {OUTPUT_FILE} gespeichert.")
