import glob
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

CONTENT_DIR = Path("content")
SCHEMA_DIR = Path("schema")
BASE_URL = "https://oliver-nix.de"
PERSON_ID = f"{BASE_URL}/#oliver-nix"
SITE_ID = f"{BASE_URL}/#website"
GLOSSARY_ID = f"{BASE_URL}/ausdauersport/glossar/#content"

YAML_EDITOR = YAML()
YAML_EDITOR.preserve_quotes = True
YAML_EDITOR.width = 4096
YAML_EDITOR.indent(mapping=4, sequence=4, offset=2)

EXCLUDED_PATH_PARTS = (
    "99-quellenverzeichnis",
    "disclaimer",
    "externe_quellen",
)


def load_central_entities():
    """Lädt Person und Website aus dem zentralen Schema-Verzeichnis."""
    entities = []

    for name in ("person", "site"):
        path = SCHEMA_DIR / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Zentrale Schema-Datei fehlt: {path}")

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Schema-Datei ist ungültig: {path}: {exc}") from exc

        entities.append(data)

    return entities


def load_yaml_document(yaml_path):
    """Lädt eine Typemill-YAML und gibt Dokument sowie meta-Block zurück."""
    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        raise FileNotFoundError(f"Zur Markdown-Datei fehlt die YAML-Datei: {yaml_path}")

    try:
        with yaml_path.open("r", encoding="utf-8") as file:
            document = YAML_EDITOR.load(file) or {}
    except Exception as exc:
        raise RuntimeError(f"YAML konnte nicht gelesen werden: {yaml_path}: {exc}") from exc

    if not isinstance(document, dict):
        raise ValueError(f"Die YAML-Wurzel muss ein Objekt sein: {yaml_path}")

    meta = document.setdefault("meta", {})
    if not isinstance(meta, dict):
        raise ValueError(f"'meta' muss ein YAML-Objekt sein: {yaml_path}")

    return document, meta


def strip_markdown(text):
    """Entfernt einfache Markdown-Auszeichnung für Beschreibungen und Antworten."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_faqs(md_content):
    """Extrahiert sichtbare H3-Fragen aus einem FAQ- oder Häufige-Fragen-Abschnitt."""
    faqs = []
    in_faq = False
    current_question = None
    current_answer = []

    def save_current():
        if current_question and current_answer:
            answer = strip_markdown(" ".join(current_answer))
            if answer:
                faqs.append({"q": current_question, "a": answer})

    for raw_line in md_content.splitlines():
        line = raw_line.strip()

        if line.startswith("## "):
            heading = line[3:].strip().lower()
            if "häufige fragen" in heading or heading in {"faq", "faqs"}:
                in_faq = True
                continue
            if in_faq:
                break

        if not in_faq:
            continue

        if line.startswith("### "):
            save_current()
            question = strip_markdown(line[4:])
            question = re.sub(r"^frage\s*\d*\s*:?\s*", "", question, flags=re.IGNORECASE)
            if question and not question.endswith("?"):
                question += "?"
            current_question = question or None
            current_answer = []
            continue

        if current_question and line:
            cleaned = re.sub(
                r"^antwort\s*\d*\s*:?\s*",
                "",
                line,
                flags=re.IGNORECASE,
            )
            current_answer.append(cleaned)

    save_current()
    return faqs


def determine_page_type(md_path):
    """Leitet den primären Inhaltstyp aus Dateiname und Pfad ab."""
    md_path = Path(md_path)
    filename = md_path.name.lower()
    path_text = md_path.as_posix().lower()

    if "glossar" in filename or "/glossar/" in path_text:
        return ["CollectionPage", "DefinedTermSet"]

    if filename == "index.md":
        return ["CollectionPage"]

    return ["Article"]


def clean_segment(segment):
    """Entfernt ausschließlich führende Typemill-Sortierungspräfixe."""
    return re.sub(r"^\d{2}-", "", segment)


def build_page_url(md_path):
    """Erzeugt eine kanonische URL aus dem Typemill-Dateipfad."""
    md_path = Path(md_path)
    relative = md_path.relative_to(CONTENT_DIR)
    parts = [clean_segment(part) for part in relative.parts]

    if parts[-1] == "index.md":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem

    clean_path = "/".join(part for part in parts if part)
    if not clean_path:
        return f"{BASE_URL}/"

    return urljoin(f"{BASE_URL}/", f"{clean_path}/")


def build_description(md_content, meta, title):
    description = str(meta.get("description") or "").strip()
    if description:
        return strip_markdown(description)

    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", md_content):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph.startswith(("#", "![", "```", "*Hinweis:")):
            continue
        cleaned = strip_markdown(paragraph)
        if cleaned:
            paragraphs.append(cleaned)

    if not paragraphs:
        return f"Sportwissenschaftliche Einordnung zu {title}."

    first = paragraphs[0]
    return first if len(first) <= 160 else f"{first[:157].rstrip()}..."


def build_breadcrumb(md_path, page_url, title):
    """Erzeugt eine einfache BreadcrumbList aus der Typemill-Pfadstruktur."""
    relative = Path(md_path).relative_to(CONTENT_DIR)
    raw_parts = list(relative.parts)

    if raw_parts[-1] == "index.md":
        raw_parts = raw_parts[:-1]
    else:
        raw_parts[-1] = Path(raw_parts[-1]).stem

    items = [{
        "@type": "ListItem",
        "position": 1,
        "name": "Startseite",
        "item": f"{BASE_URL}/",
    }]

    current_parts = []
    for position, raw_part in enumerate(raw_parts, start=2):
        clean_part = clean_segment(raw_part)
        current_parts.append(clean_part)
        name = clean_part.replace("-", " ").strip().title()
        item_url = urljoin(f"{BASE_URL}/", "/".join(current_parts) + "/")
        items.append({
            "@type": "ListItem",
            "position": position,
            "name": title if item_url == page_url else name,
            "item": item_url,
        })

    return {
        "@type": "BreadcrumbList",
        "@id": f"{page_url}#breadcrumb",
        "itemListElement": items,
    }


def build_graph(md_path, meta, central_entities):
    with Path(md_path).open("r", encoding="utf-8") as file:
        md_content = file.read()

    title_match = re.search(r"^#\s+(.+)$", md_content, re.MULTILINE)
    title = str(meta.get("title") or "").strip()
    if not title:
        title = title_match.group(1).strip() if title_match else Path(md_path).stem

    title = strip_markdown(title)
    description = build_description(md_content, meta, title)
    page_url = build_page_url(md_path)
    page_types = determine_page_type(md_path)

    graph = list(central_entities)

    webpage_node = {
        "@type": "WebPage",
        "@id": f"{page_url}#webpage",
        "url": page_url,
        "name": title,
        "headline": title,
        "description": description,
        "inLanguage": "de-DE",
        "isPartOf": {"@id": SITE_ID},
        "breadcrumb": {"@id": f"{page_url}#breadcrumb"},
        "mainEntity": {"@id": f"{page_url}#content"},
    }
    graph.append(webpage_node)

    main_entity = {
        "@type": page_types,
        "@id": f"{page_url}#content",
        "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
        "headline": title,
        "name": title,
        "description": description,
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": SITE_ID},
        "isPartOf": {"@id": SITE_ID},
        "inLanguage": "de-DE",
        "publishingPrinciples": f"{BASE_URL}/ausdauersport/disclaimer/",
    }

    if meta.get("created"):
        main_entity["datePublished"] = str(meta["created"])
    if meta.get("modified"):
        main_entity["dateModified"] = str(meta["modified"])

    if "DefinedTermSet" in page_types:
        main_entity["url"] = page_url
    elif "DefinedTerm" in page_types:
        main_entity["inDefinedTermSet"] = {"@id": GLOSSARY_ID}

    graph.append(main_entity)
    graph.append(build_breadcrumb(md_path, page_url, title))

    faqs = extract_faqs(md_content)
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "@id": f"{page_url}#faq",
            "isPartOf": {"@id": f"{page_url}#webpage"},
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq["q"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": faq["a"],
                    },
                }
                for faq in faqs
            ],
        })

    return {"@context": "https://schema.org", "@graph": graph}


def write_jsonld_to_yaml(yaml_path, document, meta, page_graph):
    """Schreibt den Graph als Literalblock nach meta.json_ld."""
    yaml_path = Path(yaml_path)
    json_ld = json.dumps(page_graph, indent=2, ensure_ascii=False)
    meta["json_ld"] = LiteralScalarString(json_ld)

    temporary_path = yaml_path.with_suffix(".yaml.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            YAML_EDITOR.dump(document, file)
        os.replace(temporary_path, yaml_path)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise


def run():
    central_entities = load_central_entities()
    md_files = sorted(glob.glob(str(CONTENT_DIR / "**" / "*.md"), recursive=True))

    processed = 0
    skipped = 0

    for md_path_text in md_files:
        md_path = Path(md_path_text)
        normalized_path = md_path.as_posix().lower()

        if any(part in normalized_path for part in EXCLUDED_PATH_PARTS):
            skipped += 1
            continue

        yaml_path = md_path.with_suffix(".yaml")
        document, meta = load_yaml_document(yaml_path)
        page_graph = build_graph(md_path, meta, central_entities)
        write_jsonld_to_yaml(yaml_path, document, meta, page_graph)
        processed += 1

    print(f"JSON-LD in {processed} Typemill-YAML-Dateien aktualisiert; {skipped} Seiten übersprungen.")


if __name__ == "__main__":
    run()
