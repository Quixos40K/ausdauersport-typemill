#!/usr/bin/env python3
"""Generate Schema.org JSON-LD for a Markdown bibliography.

The parser is deliberately conservative:
- every Markdown bullet beginning with "* " is one visible source entry;
- the complete visible citation is preserved as text;
- URLs are copied from the Markdown and never invented;
- no source is classified as ScholarlyArticle unless that is added later
  through a stricter, normalized source format.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
RAW_URL_RE = re.compile(r"https?://[^\s)>,]+")
MARKDOWN_DECORATION_RE = re.compile(r"[*_`]")
MULTISPACE_RE = re.compile(r"\s+")

GENERIC_LINK_LABELS = {
    "pubmed",
    "pmc",
    "springer",
    "frontiers",
    "nature",
    "sciencedirect",
    "human kinetics",
    "bjsm",
    "doi",
    "pdf",
    "quelle",
    "link",
    "article",
    "full text",
    "fulltext",
    "europe pmc",
}


def normalize_url(url: str) -> str:
    """Normalize a URL only enough for duplicate detection."""
    url = html.unescape(url.strip())
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = re.sub(r"/{2,}", "/", parts.path)
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def extract_urls(entry: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for _, url in MARKDOWN_LINK_RE.findall(entry):
        clean = html.unescape(url.strip())
        key = normalize_url(clean)
        if key not in seen:
            seen.add(key)
            urls.append(clean)

    without_markdown_links = MARKDOWN_LINK_RE.sub("", entry)
    for url in RAW_URL_RE.findall(without_markdown_links):
        clean = html.unescape(url.rstrip(".,;"))
        key = normalize_url(clean)
        if key not in seen:
            seen.add(key)
            urls.append(clean)

    return urls


def clean_visible_text(entry: str) -> str:
    """Convert one Markdown bibliography bullet into plain visible text."""
    text = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), entry)
    text = RAW_URL_RE.sub("", text)
    text = MARKDOWN_DECORATION_RE.sub("", text)
    text = text.replace("Quelle:", "")
    text = MULTISPACE_RE.sub(" ", text)
    return text.strip(" .;,-")


def derive_name(entry: str) -> str:
    """Use an explicit title link when available; otherwise preserve citation text."""
    links = MARKDOWN_LINK_RE.findall(entry)
    for label, _ in links:
        candidate = MULTISPACE_RE.sub(" ", MARKDOWN_DECORATION_RE.sub("", label)).strip()
        if candidate and candidate.casefold() not in GENERIC_LINK_LABELS and len(candidate) >= 12:
            return candidate

    before_source = re.split(r"\bQuelle:\s*", entry, maxsplit=1)[0]
    candidate = clean_visible_text(before_source)
    if candidate:
        return candidate
    return clean_visible_text(entry)


def read_entries(markdown_path: Path) -> list[str]:
    text = markdown_path.read_text(encoding="utf-8")
    entries = [line[2:].strip() for line in text.splitlines() if line.startswith("* ")]
    if not entries:
        raise ValueError(f"Keine Quellenzeilen mit '* ' in {markdown_path} gefunden.")
    return entries


def build_item_list(entries: list[str]) -> tuple[list[dict], dict]:
    items: list[dict] = []
    url_positions: dict[str, list[int]] = defaultdict(list)
    warnings: list[dict] = []

    for position, entry in enumerate(entries, start=1):
        urls = extract_urls(entry)
        if not urls:
            raise ValueError(
                f"Quelle an Position {position} enthält keine HTTP(S)-URL: {entry}"
            )

        primary_url = urls[0]
        normalized_primary = normalize_url(primary_url)
        url_positions[normalized_primary].append(position)

        visible_citation = clean_visible_text(entry)
        name = derive_name(entry)

        work: dict[str, object] = {
            "@type": "CreativeWork",
            "@id": primary_url,
            "name": name,
            "url": primary_url if len(urls) == 1 else urls,
            "description": visible_citation,
        }

        if len(urls) > 1:
            warnings.append(
                {
                    "type": "multiple_urls",
                    "position": position,
                    "urls": urls,
                }
            )

        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "item": work,
            }
        )

    duplicates = {
        url: positions
        for url, positions in url_positions.items()
        if len(positions) > 1
    }

    report = {
        "source_entries": len(entries),
        "generated_items": len(items),
        "duplicate_primary_urls": duplicates,
        "duplicate_primary_url_count": len(duplicates),
        "warnings": warnings,
    }
    return items, report


def build_graph(
    *,
    page_url: str,
    page_name: str,
    description: str,
    person_id: str,
    person_name: str,
    person_url: str,
    website_id: str,
    website_name: str,
    website_url: str,
    disclaimer_url: str | None,
    items: list[dict],
) -> dict:
    page_url = page_url.rstrip("/") + "/"
    website_url = website_url.rstrip("/") + "/"

    webpage_id = f"{page_url}#webpage"
    list_id = f"{page_url}#quellenliste"
    breadcrumb_id = f"{page_url}#breadcrumb"

    webpage: dict[str, object] = {
        "@type": "CollectionPage",
        "@id": webpage_id,
        "url": page_url,
        "name": page_name,
        "headline": page_name,
        "description": description,
        "inLanguage": "de-DE",
        "isAccessibleForFree": True,
        "isPartOf": {"@id": website_id},
        "author": {"@id": person_id},
        "publisher": {"@id": person_id},
        "breadcrumb": {"@id": breadcrumb_id},
        "mainEntity": {"@id": list_id},
        "about": [
            {"@type": "Thing", "name": "Ausdauersport"},
            {"@type": "Thing", "name": "Sportmedizin"},
            {"@type": "Thing", "name": "Trainingsphysiologie"},
            {"@type": "Thing", "name": "Biomechanik"},
            {"@type": "Thing", "name": "Orthopädie"},
        ],
    }
    if disclaimer_url:
        webpage["publishingPrinciples"] = disclaimer_url

    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Person",
                "@id": person_id,
                "name": person_name,
                "url": person_url,
            },
            {
                "@type": "WebSite",
                "@id": website_id,
                "url": website_url,
                "name": website_name,
                "inLanguage": "de-DE",
                "publisher": {"@id": person_id},
            },
            webpage,
            {
                "@type": "ItemList",
                "@id": list_id,
                "url": page_url,
                "name": "Wissenschaftliche Quellen des Ausdauersport-Projekts",
                "description": "Sammlung der im Ausdauersport-Projekt verwendeten wissenschaftlichen Quellen.",
                "numberOfItems": len(items),
                "itemListElement": items,
                "mainEntityOfPage": {"@id": webpage_id},
            },
            {
                "@type": "BreadcrumbList",
                "@id": breadcrumb_id,
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Startseite",
                        "item": website_url,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": page_name,
                        "item": page_url,
                    },
                ],
            },
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Erzeugt vollständiges JSON-LD aus einem Markdown-Quellenverzeichnis."
    )
    parser.add_argument("source", type=Path, help="Pfad zur Markdown-Datei")
    parser.add_argument("output", type=Path, help="Zieldatei für JSON-LD")
    parser.add_argument(
        "--report",
        type=Path,
        help="Optionale JSON-Prüfdatei mit Dubletten und Warnungen",
    )
    parser.add_argument(
        "--page-url",
        required=True,
        help="Kanonische URL des Quellenverzeichnisses",
    )
    parser.add_argument(
        "--page-name",
        default="Wissenschaftliches Quellenverzeichnis",
    )
    parser.add_argument(
        "--description",
        default=(
            "Wissenschaftliches Quellenverzeichnis mit sportmedizinischer, "
            "physiologischer und biomechanischer Fachliteratur aus den Artikeln "
            "des Ausdauersport-Projekts."
        ),
    )
    parser.add_argument("--person-id", default="https://www.oliver-nix.de/#person")
    parser.add_argument("--person-name", default="Oliver Nix")
    parser.add_argument("--person-url", default="https://www.oliver-nix.de/")
    parser.add_argument("--website-id", default="https://www.oliver-nix.de/#website")
    parser.add_argument("--website-name", default="Oliver Nix")
    parser.add_argument("--website-url", default="https://www.oliver-nix.de/")
    parser.add_argument("--disclaimer-url")
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Mit Fehler abbrechen, wenn dieselbe primäre URL mehrfach vorkommt",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        entries = read_entries(args.source)
        items, report = build_item_list(entries)
        graph = build_graph(
            page_url=args.page_url,
            page_name=args.page_name,
            description=args.description,
            person_id=args.person_id,
            person_name=args.person_name,
            person_url=args.person_url,
            website_id=args.website_id,
            website_name=args.website_name,
            website_url=args.website_url,
            disclaimer_url=args.disclaimer_url,
            items=items,
        )
    except (OSError, ValueError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    duplicate_count = report["duplicate_primary_url_count"]
    print(
        f"Erzeugt: {args.output} | Quellen: {len(items)} | "
        f"doppelte primäre URLs: {duplicate_count}"
    )

    if args.fail_on_duplicates and duplicate_count:
        print(
            "FEHLER: Doppelte primäre URLs gefunden. Details stehen im Report.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
