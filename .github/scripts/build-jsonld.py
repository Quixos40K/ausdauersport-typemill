import os
import glob
import json
import re
import yaml

CONTENT_DIR = "content"
SCHEMA_DIR = "schema"
BASE_URL = "https://deine-domain.de" # Hier deine echte Domain eintragen
PERSON_ID = f"{BASE_URL}/#oliver-nix"
SITE_ID = f"{BASE_URL}/#website"

def load_central_entities():
    entities = []
    for name in ["person", "site"]:
        path = os.path.join(SCHEMA_DIR, f"{name}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                entities.append(json.load(f))
    return entities

def build_graph(md_path, yaml_path, central_entities):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 1. Schlanke YAML-Metadaten einlesen
    yaml_data = {}
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            try:
                yaml_data = yaml.safe_load(f) or {}
            except Exception:
                pass

    # 2. Variablen isolieren (YAML First, Markdown Fallback)
    title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
    title = yaml_data.get('title') or (title_match.group(1).strip() if title_match else os.path.basename(md_path).replace('.md', ''))

    description = yaml_data.get('description') or ""
    if not description:
        paragraphs = [p.strip() for p in md_content.split('\n\n') if p.strip() and not p.startswith('#') and not p.startswith('![')]
        description = paragraphs[0][:157] + "..." if paragraphs else f"Sportwissenschaftliche Evidenz zu {title}."

    # 3. URL-Pfad bereinigen (Typemill-Sortierpräfixe entfernen)
    clean_path = re.sub(r'\d{2}-', '', md_path.replace('content/', '').replace('.md', ''))
    filename = os.path.basename(md_path)
    is_index = filename == "index.md"
    if is_index:
        clean_path = os.path.dirname(clean_path)
    
    page_url = f"{BASE_URL}/{clean_path.replace(os.sep, '/')}"

    # 4. Präzise Schema-Typisierung
    if "glossar" in md_path.lower():
        primary_type = "DefinedTermSet" if is_index else "DefinedTerm"
    else:
        primary_type = "CollectionPage" if is_index else "Article"

    # 5. Den Graphen orchestrieren
    graph = list(central_entities)

    # Der WebPage-Knoten
    webpage_node = {
        "@type": "WebPage",
        "@id": f"{page_url}#webpage",
        "url": page_url,
        "headline": title,
        "isPartOf": {"@id": SITE_ID}
    }
    graph.append(webpage_node)

    # Der semantische Inhalts-Knoten
    main_entity = {
        "@type": primary_type,
        "@id": f"{page_url}#content",
        "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
        "headline": title,
        "description": description,
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": SITE_ID},
        "inLanguage": "de-DE"
    }

    # Redaktionelle Zeitstempel aus YAML
    if yaml_data.get('created'):
        main_entity["datePublished"] = str(yaml_data.get('created'))
    if yaml_data.get('modified'):
        main_entity["dateModified"] = str(yaml_data.get('modified'))

    # Typ-spezifische Verbindungen
    if primary_type == "Article":
        webpage_node["mainEntity"] = {"@id": f"{page_url}#content"}

    if primary_type == "DefinedTerm":
        main_entity["name"] = title
        main_entity["inDefinedTermSet"] = {"@id": f"{BASE_URL}/glossar#content"}
        webpage_node["mainEntity"] = {"@id": f"{page_url}#content"}

    graph.append(main_entity)

    # 6. FAQ als sekundäres Signal (falls vorhanden)
    if '## Häufige Fragen' in md_content:
        faq_block = md_content.split('## Häufige Fragen')[1].split('##')[0]
        matches = re.findall(r'(?:\*\*Frage:\*\*|\*\*(.*?)\?\*\*)\s*(.*?)(?=\*\*Frage:\*\*|\*\*(.*?)\?\*\*|$)', faq_block, re.DOTALL)
        faqs = []
        for match in matches:
            q = match[0].strip() if match[0] else ""
            a = match[1].replace('**Antwort:**', '').strip() if match[1] else ""
            if q and a:
                faqs.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
        
        if faqs:
            graph.append({
                "@type": "FAQPage",
                "@id": f"{page_url}#faq",
                "mainEntity": faqs,
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
        
        # Sidecar-JSON Datei generieren
        json_path = md_path.replace('.md', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(page_graph, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    run()
