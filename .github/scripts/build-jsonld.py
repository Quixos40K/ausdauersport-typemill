import os
import glob
import json
import re
import yaml

CONTENT_DIR = "content"
SCHEMA_DIR = "schema"
BASE_URL = "https://oliver-nix.de"
PERSON_ID = f"{BASE_URL}/#oliver-nix"
SITE_ID = f"{BASE_URL}/#website"

def load_central_entities():
    """Lädt die globalen Konstanten und korrigiert die URIs auf die Ziel-Domain."""
    entities = []
    for name in ["person", "site"]:
        path = os.path.join(SCHEMA_DIR, f"{name}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Domänenspezifische Umschreibung zur Absicherung der SSOT
                if "@id" in data:
                    data["@id"] = data["@id"].replace("https://deine-domain.de", BASE_URL)
                if "url" in data:
                    data["url"] = data["url"].replace("https://deine-domain.de", BASE_URL)
                if "sameAs" in data:
                    data["sameAs"] = [link.replace("https://deine-domain.de", BASE_URL) for link in data["sameAs"]]
                if "publisher" in data and isinstance(data["publisher"], dict) and "@id" in data["publisher"]:
                    data["publisher"]["@id"] = data["publisher"]["@id"].replace("https://deine-domain.de", BASE_URL)
                entities.append(data)
    return entities

def extract_faqs(md_content):
    """Extrahiert FAQs vollautomatisch und fehlertolerant über Regex-Splitting."""
    faqs = []
    # Erkennt flexibel: '## Häufige Fragen', '## FAQ', '## FAQs', '## Häufige Fragen zur...'
    heading_match = re.search(r'##\s*(?:Häufige\s+Fragen|FAQ)[^\n]*', md_content, re.IGNORECASE)
    
    if heading_match:
        post_heading = md_content[heading_match.end():]
        # Trennt den Block sauber bei der nächsten H2-Überschrift ab
        faq_block = re.split(r'\n##\s+', post_heading)[0]
        
        # Splittet den Block bei allen erdenklichen Varianten von "Frage" (fett, H3, mit Zahlen)
        raw_items = re.split(r'(?:\#\#\#\s*Frage|__Frage__|__Frage\s*\d+__|__Frage:__|__Frage\s*\d+:__|\*\*Frage|\*\*Frage\s*\d+|\*\*Frage:|\*\*Frage\s*\d+:)', faq_block, flags=re.IGNORECASE)
        
        for item in raw_items[1:]:
            # Sucht den passenden Antwort-Marker innerhalb dieses Abschnitts
            answer_match = re.search(r'(?:\#\#\#\s*Antwort|__Antwort__|__Antwort:__|\*\*Antwort|\*\*Antwort:)', item, flags=re.IGNORECASE)
            if answer_match:
                q_part = item[:answer_match.start()]
                a_part = item[answer_match.end():]
                
                # Bereinigt nackte Zahlen, Doppelpunkte und Formatierungszeichen am Anfang der Frage
                q_clean = re.sub(r'^[\d\s\:\*\#\-\_\?]+', '', q_part).strip()
                q_clean = q_clean.rstrip('*_ :?')
                if q_clean:
                    q_clean += "?" # Standardisiertes Satzzeichen für Entitäten-Titel
                
                # Bereinigt die dazugehörige Antwort von führenden Sonderzeichen
                a_clean = re.sub(r'^[\d\s\:\*\#\-\_]+', '', a_part).strip()
                a_clean = a_clean.rstrip('*_ ')
                
                if q_clean and a_clean and len(q_clean) > 3:
                    faqs.append({"q": q_clean, "a": a_clean})
    return faqs

def determine_page_type(filepath, yaml_data):
    filename = os.path.basename(filepath)
    path_segments = filepath.split(os.sep)
    
    if "glossar" in "".join(path_segments).lower():
        if filename == "index.md":
            return ["CollectionPage", "DefinedTermSet"]
        return ["DefinedTerm"]
        
    if filename == "index.md":
        return ["CollectionPage"]
    
    return ["MedicalWebPage", "Article"]

def build_graph(md_path, yaml_path, central_entities):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    yaml_data = {}
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            try:
                yaml_data = yaml.safe_load(f) or {}
            except Exception:
                pass

    title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
    title = yaml_data.get('title') or (title_match.group(1).strip() if title_match else os.path.basename(md_path).replace('.md', ''))

    description = yaml_data.get('description') or ""
    if not description:
        paragraphs = [p.strip() for p in md_content.split('\n\n') if p.strip() and not p.startswith('#') and not p.startswith('![')]
        description = paragraphs[0][:157] + "..." if paragraphs else f"Sportwissenschaftliche Evidenz zu {title}."

    # Pfad-Normalisierung (Entfernung der Typemill-Sortierungspräfixe wie 00-)
    clean_path = re.sub(r'\d{2}-', '', md_path.replace('content/', '').replace('.md', ''))
    filename = os.path.basename(md_path)
    is_index = filename == "index.md"
    if is_index:
        clean_path = os.path.dirname(clean_path)
    
    page_url = f"{BASE_URL}/{clean_path.replace(os.sep, '/')}"
    page_types = determine_page_type(md_path, yaml_data)

    graph = list(central_entities)

    webpage_node = {
        "@type": "WebPage",
        "@id": f"{page_url}#webpage",
        "url": page_url,
        "headline": title,
        "isPartOf": {"@id": SITE_ID}
    }
    graph.append(webpage_node)

    main_entity = {
        "@type": page_types,
        "@id": f"{page_url}#content",
        "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
        "headline": title,
        "description": description,
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": SITE_ID},
        "inLanguage": "de-DE"
    }

    if yaml_data.get('created'):
        main_entity["datePublished"] = str(yaml_data.get('created'))
    if yaml_data.get('modified'):
        main_entity["dateModified"] = str(yaml_data.get('modified'))

    if "Article" in page_types:
        webpage_node["mainEntity"] = {"@id": f"{page_url}#content"}

    if "DefinedTerm" in page_types:
        main_entity["name"] = title
        main_entity["inDefinedTermSet"] = {"@id": f"{BASE_URL}/glossar#content"}
        webpage_node["mainEntity"] = {"@id": f"{page_url}#content"}

    graph.append(main_entity)

    # Fehlertolerante FAQ-Extraktion ausführen
    faqs = extract_faqs(md_content)
    if faqs:
        faq_entities = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
        graph.append({
            "@type": "FAQPage",
            "@id": f"{page_url}#faq",
            "mainEntity": faq_entities,
            "isPartOf": {"@id": f"{page_url}#webpage"}
        })

    return {"@context": "https://schema.org", "@graph": graph}

def run():
    central_entities = load_central_entities()
    md_files = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)
    
    for md_path in md_files:
        if "99-quellenverzeichnis" in md_path.lower() or "disclaimer" in md_path.lower() or "externe_quellen" in md_path.lower():
            continue
            
        yaml_path = md_path.replace('.md', '.yaml')
        page_graph = build_graph(md_path, yaml_path, central_entities)
        
        json_path = md_path.replace('.md', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(page_graph, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    run()
