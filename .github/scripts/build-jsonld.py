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
    entities = []
    for name in ["person", "site"]:
        path = os.path.join(SCHEMA_DIR, f"{name}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
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
    faqs = []
    lines = md_content.split('\n')
    in_faq = False
    current_q = ""
    current_a = []
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Startschuss: Ist das die FAQ-Sektion?
        if stripped.startswith('## '):
            if 'häufige fragen' in stripped.lower() or 'faq' in stripped.lower():
                in_faq = True
                continue
            elif in_faq:
                # Eine neue H2-Überschrift beendet den FAQ-Bereich
                break
                
        if in_faq and stripped:
            is_question = False
            lower = stripped.lower()
            
            # Erkennung 1: Das Wort "Frage" steht in einer fetten Zeile
            if 'frage' in lower and ('**' in lower or '###' in lower or '__' in lower):
                is_question = True
            # Erkennung 2: Die Zeile ist fett/H3 und enthält ein Fragezeichen (auch ohne das Wort "Frage")
            elif (stripped.startswith('**') or stripped.startswith('- **') or stripped.startswith('__') or stripped.startswith('###')) and '?' in stripped:
                is_question = True
                
            if is_question:
                # Vorheriges Frage-Antwort-Paar speichern
                if current_q and current_a:
                    faqs.append({"q": current_q, "a": " ".join(current_a)})
                
                # Neue Frage bereinigen (Sterne, Rauten, "Frage:" entfernen)
                q_clean = re.sub(r'^[\*\#\-\_\s]+', '', stripped)
                q_clean = re.sub(r'[\*\#\-\_\s]+$', '', q_clean)
                q_clean = re.sub(r'^(?i)(Frage\s*\d*:?|Frage:)\s*', '', q_clean)
                current_q = q_clean.strip()
                if not current_q.endswith('?'):
                    current_q += '?'
                current_a = []
            else:
                # Es ist keine Frage, also muss es die Antwort sein
                if current_q:
                    a_clean = re.sub(r'^[\*\#\-\_\s]+', '', stripped)
                    a_clean = re.sub(r'^(?i)(Antwort\s*\d*:?|Antwort:)\s*', '', a_clean)
                    a_clean = re.sub(r'[\*\#\-\_]+$', '', a_clean) # Trailing Markdown entfernen
                    if a_clean:
                        current_a.append(a_clean.strip())
                        
    # Den letzten Block der Schleife speichern
    if current_q and current_a:
        faqs.append({"q": current_q, "a": " ".join(current_a)})
        
    return faqs

def determine_page_type(filepath, yaml_data):
    filename = os.path.basename(filepath)
    path_segments = filepath.split(os.sep)
    if "glossar" in "".join(path_segments).lower():
        return ["CollectionPage", "DefinedTermSet"] if filename == "index.md" else ["DefinedTerm"]
    return ["CollectionPage"] if filename == "index.md" else ["MedicalWebPage", "Article"]

def build_graph(md_path, yaml_path, central_entities):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    yaml_data = {}
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            try: yaml_data = yaml.safe_load(f) or {}
            except Exception: pass

    title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
    title = yaml_data.get('title') or (title_match.group(1).strip() if title_match else os.path.basename(md_path).replace('.md', ''))

    description = yaml_data.get('description') or ""
    if not description:
        paragraphs = [p.strip() for p in md_content.split('\n\n') if p.strip() and not p.startswith('#') and not p.startswith('![')]
        description = paragraphs[0][:157] + "..." if paragraphs else f"Sportwissenschaftliche Evidenz zu {title}."

    clean_path = re.sub(r'\d{2}-', '', md_path.replace('content/', '').replace('.md', ''))
    filename = os.path.basename(md_path)
    if filename == "index.md": clean_path = os.path.dirname(clean_path)
    
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

    if yaml_data.get('created'): main_entity["datePublished"] = str(yaml_data.get('created'))
    if yaml_data.get('modified'): main_entity["dateModified"] = str(yaml_data.get('modified'))

    if "Article" in page_types: webpage_node["mainEntity"] = {"@id": f"{page_url}#content"}
    if "DefinedTerm" in page_types:
        main_entity["name"] = title
        main_entity["inDefinedTermSet"] = {"@id": f"{BASE_URL}/glossar#content"}
        webpage_node["mainEntity"] = {"@id": f"{page_url}#content"}

    graph.append(main_entity)

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
        if "99-quellenverzeichnis" in md_path.lower() or "disclaimer" in md_path.lower() or "externe_quellen" in md_path.lower(): continue
        yaml_path = md_path.replace('.md', '.yaml')
        page_graph = build_graph(md_path, yaml_path, central_entities)
        json_path = md_path.replace('.md', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(page_graph, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    run()
