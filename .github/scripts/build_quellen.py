import os
import glob
import re

CONTENT_DIR = "content"
OUTPUT_FILE = "content/00-ausdauersport/99-quellenverzeichnis.md"

def absolute_cleaner(text):
    # 1. HTML-Tags entfernen
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. Die brutale Schleife für den Anfang des Textes
    while True:
        original = text
        text = text.strip()
        
        # Entfernt alle Markdown-Sonderzeichen am Anfang (#, *, -, >)
        text = re.sub(r'^[\#\*\-\>\s]+', '', text)
        
        # Entfernt das Wort "Quelle" mit eventuellen Zahlen und Sonderzeichen (z.B. "Quelle 1:", "Quelle 1 -")
        text = re.sub(r'^Quelle\s*\d*\s*[:\-–]?\s*', '', text, flags=re.IGNORECASE)
        
        # Entfernt eckige oder runde Klammern mit Zahlen am Anfang (z.B. "[9]", "(12)")
        text = re.sub(r'^[\(\[]\s*\d+\s*[\)\]]\s*[:\-–]?\s*', '', text)
        
        # Entfernt nackte Zahlen mit Punkt oder Bindestrich am Anfang (z.B. "1. ", "9 - ")
        text = re.sub(r'^\d+\s*[\.\-–\:]\s+', '', text)
        
        # Wenn die Schleife nichts mehr findet, brich ab
        if text == original:
            break
            
    return text.strip()

def extract_sources():
    all_sources = set()
    md_files = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)
    
    for filepath in md_files:
        # Systemdateien überspringen
        if "99-quellenverzeichnis" in filepath.lower() or "disclaimer" in filepath.lower() or "externe_quellen" in filepath.lower():
            continue
            
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        if '## Quellen' in content:
            quellen_block = content.split('## Quellen')[1]
            
            if 'Hinweis: Dieser Artikel' in quellen_block:
                quellen_block = quellen_block.split('Hinweis: Dieser Artikel')[0]
                
            # Zerteilen in einzelne Absätze
            blocks = quellen_block.split('\n\n')
            
            for block in blocks:
                # Zeilenumbrüche innerhalb eines Absatzes entfernen
                block = block.replace('\n', ' ').strip()
                
                # Wenn der Block einen Link enthält, jagen wir ihn durch den Cleaner
                if "http" in block:
                    cleaned = absolute_cleaner(block)
                    if cleaned:
                        all_sources.add(cleaned)

    return all_sources

def write_master_file(sources):
    # Sortiere alphabetisch
    sorted_sources = sorted(list(sources))
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Wissenschaftliches Quellenverzeichnis\n\n")
        f.write("Dieses Lexikon basiert auf der aktuellen sportmedizinischen, physiologischen und biomechanischen Primärliteratur. ")
        f.write("Die folgende Liste wird automatisch aus allen Artikeln dieses Projekts generiert und laufend aktualisiert.\n\n")
        f.write("---\n\n")
        
        for source in sorted_sources:
            f.write(f"* {source}\n\n")

if __name__ == "__main__":
    print("Starte die finale Quellen-Reinigung...")
    extracted = extract_sources()
    write_master_file(extracted)
    print(f"Erfolgreich {len(extracted)} makellose Quellen extrahiert.")
