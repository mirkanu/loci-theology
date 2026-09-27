#!/usr/bin/env python3
"""Build a static GitHub Pages site from the loci-theology taxonomy.

The site is purely a derived artefact. The source of truth is
`data/loci.ttl`. Any consumer can re-run this against a checked-out copy of
the data files.
"""
from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import rdflib

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist"

NS = {
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
    "loci": rdflib.Namespace("https://loci-theology.org/vocab/"),
    "lt": rdflib.Namespace("https://loci-theology.org/id/"),
    "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
}

# Typed relations, in display order. Each entry: (predicate, label, target_card).
# `target_card` is "single" (object property → 0..1 target) or "multi".
TYPED_RELS: list[tuple[str, str]] = [
    ("https://loci-theology.org/vocab/dependsOn", "depends on"),
    ("https://loci-theology.org/vocab/presupposes", "presupposes"),
    ("https://loci-theology.org/vocab/groundsIn", "grounds in"),
    ("https://loci-theology.org/vocab/fulfilledBy", "fulfilled by"),
    ("https://loci-theology.org/vocab/appliesTo", "applies to"),
    ("https://loci-theology.org/vocab/contrastsWith", "contrasts with"),
    ("https://loci-theology.org/vocab/distinctFrom", "distinct from"),
]

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title} · Loci Theology</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="stylesheet" href="{root}styles.css">
</head>
<body>
  <header><a href="{root}index.html">← All loci</a></header>
  <main>
    <h1>{title}</h1>
    <p class="breadcrumb">{breadcrumb}</p>
    {alt_label_html}
    {narrower_html}
    {related_html}
    {typed_html}
    {backref_html}
    <p class="iri"><code>{iri}</code></p>
  </main>
</body>
</html>
"""

INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Loci Theology — taxonomy of Christian doctrines</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="An open-source hierarchical taxonomy of Christian doctrines arranged around the six loci of dogmatics. RDF/SKOS+OWL, no content.">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header><h1>Loci Theology</h1></header>
  <main>
    <p>Hierarchical taxonomy of Christian doctrines around the six loci of dogmatics.
       Source of truth: <a href="https://github.com/mirkanu/loci-theology">github.com/mirkanu/loci-theology</a>.
       Use the <code>data/loci.ttl</code> file to tag Bible verses, hymns, or anything else.</p>
    <ul class="loci">
      {loci_list}
    </ul>
    <h2>Download</h2>
    <ul>
      <li><a href="loci.jsonld">loci.jsonld</a> — JSON-LD (web-native, drop into any RDF library)</li>
      <li><a href="loci.ttl">loci.ttl</a> — Turtle (canonical, git-diffable)</li>
      <li><a href="ontology/loci-ontology.ttl">ontology/loci-ontology.ttl</a> — OWL ontology (typed relations)</li>
    </ul>
  </main>
</body>
</html>
"""

CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       max-width: 760px; margin: 2rem auto; padding: 0 1rem; color: #1f2328; background: #fff; }
header a { color: #0969da; text-decoration: none; }
header a:hover { text-decoration: underline; }
h1 { margin-bottom: 0.25rem; }
.breadcrumb { color: #57606a; font-size: 0.95rem; margin-top: 0; }
.iri { color: #8c959f; font-size: 0.8rem; margin-top: 2rem; word-break: break-all; }
ul.loci { list-style: none; padding: 0; }
ul.loci > li { padding: 0.75rem 1rem; border: 1px solid #d0d7de; border-radius: 8px; margin: 0.5rem 0; }
ul.loci > li h2 { margin: 0 0 0.25rem 0; font-size: 1.15rem; }
ul.loci > li h2 a { color: #0969da; text-decoration: none; }
ul.loci > li p { margin: 0.25rem 0 0 0; color: #57606a; }
section { margin-top: 1.5rem; }
section h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; color: #57606a; }
section ul { padding-left: 1.25rem; }
section li { margin: 0.25rem 0; }
.alt-label { color: #57606a; font-style: italic; }
"""


def slug(uri: str) -> str:
    """Map a concept IRI to a stable URL path."""
    return quote(uri.removeprefix("https://loci-theology.org/id/"), safe="")


def href(uri: str) -> str:
    return f"concepts/{slug(uri)}.html"


def label_for(g: rdflib.Graph, uri: str) -> str:
    label = g.value(uri, NS["skos"].prefLabel)
    if label is None:
        return uri.rsplit("/", 1)[-1]
    return str(label)


def collect_concepts(g: rdflib.Graph) -> dict[str, dict]:
    """Build per-concept metadata."""
    out: dict[str, dict] = defaultdict(lambda: {
        "iri": None,
        "label": None,
        "alt_labels": [],
        "broader": [],
        "narrower": [],
        "related": [],
        "typed": defaultdict(list),  # predicate URI → list of target URIs
        "backrefs": defaultdict(list),  # predicate URI → list of source URIs
        "type": [],
        "locus": None,  # root locus (walk up skos:broader chain)
    })
    for s, p, o in g.triples((None, rdflib.RDF.type, NS["skos"].Concept)):
        out[str(s)]["iri"] = str(s)
        out[str(s)]["type"].append("Concept")
        # detect Locus / Doctrine / Topic
        for t in g.objects(s, rdflib.RDF.type):
            local = str(t).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            if local in ("Locus", "Doctrine", "Topic"):
                out[str(s)]["type"].append(local)
    for s, _, o in g.triples((None, NS["skos"].prefLabel, None)):
        out[str(s)]["label"] = str(o)
    for s, _, o in g.triples((None, NS["skos"].altLabel, None)):
        out[str(s)]["alt_labels"].append(str(o))
    for s, _, o in g.triples((None, NS["skos"].broader, None)):
        out[str(s)]["broader"].append(str(o))
        out[str(o)]["narrower"].append(str(s))
    for s, _, o in g.triples((None, NS["skos"].related, None)):
        out[str(s)]["related"].append(str(o))
        out[str(o)]["related"].append(str(s))
    for pred_uri, _ in TYPED_RELS:
        for s, _, o in g.triples((None, rdflib.URIRef(pred_uri), None)):
            out[str(s)]["typed"][pred_uri].append(str(o))
            out[str(o)]["backrefs"][pred_uri].append(str(s))
    # Compute root locus (top of broader chain, stopping at Locus).
    for iri in list(out.keys()):
        chain = []
        cur = iri
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            parents = [str(b) for b in g.objects(rdflib.URIRef(cur), NS["skos"].broader)]
            if not parents:
                break
            cur = parents[0]
        # Walk back to find Locus
        root = iri
        for node in chain:
            if "Locus" in out[node]["type"]:
                root = node
                break
        out[iri]["locus"] = root
    return out


def render_page(g: rdflib.Graph, iri: str, meta: dict) -> str:
    label = meta["label"] or iri.rsplit("/", 1)[-1]
    # breadcrumb: walk up via broader chain
    crumbs = []
    cur = iri
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        crumbs.append((cur, label_for(g, cur)))
        parents = [str(b) for b in g.objects(rdflib.URIRef(cur), NS["skos"].broader)]
        if not parents:
            break
        cur = parents[0]
    crumbs.reverse()
    breadcrumb = " / ".join(
        f'<a href="{href(c)}">{lbl}</a>' for c, lbl in crumbs
    )

    alt_label_html = ""
    if meta["alt_labels"]:
        alt_label_html = (
            f'<p class="alt-label">Also: '
            + ", ".join(meta["alt_labels"])
            + "</p>"
        )

    narrower_html = ""
    narrower_sorted = sorted(
        meta["narrower"],
        key=lambda x: (label_for(g, x).lower()),
    )
    if narrower_sorted:
        items = "".join(
            f'<li><a href="{href(c)}">{label_for(g, c)}</a></li>'
            for c in narrower_sorted
        )
        narrower_html = f'<section><h2>Narrower</h2><ul>{items}</ul></section>'

    related_html = ""
    related_sorted = sorted(meta["related"], key=lambda x: label_for(g, x).lower())
    if related_sorted:
        items = "".join(
            f'<li><a href="{href(c)}">{label_for(g, c)}</a></li>'
            for c in related_sorted
        )
        related_html = f'<section><h2>Related (skos)</h2><ul>{items}</ul></section>'

    typed_html = ""
    typed_parts = []
    for pred_uri, pred_label in TYPED_RELS:
        targets = meta["typed"].get(pred_uri, [])
        if not targets:
            continue
        items = "".join(
            f'<li>{pred_label} <a href="{href(c)}">{label_for(g, c)}</a></li>'
            for c in sorted(targets, key=lambda x: label_for(g, x).lower())
        )
        typed_parts.append(
            f'<section><h2>{pred_label.capitalize()}</h2><ul>{items}</ul></section>'
        )
    typed_html = "".join(typed_parts)

    backref_parts = []
    for pred_uri, pred_label in TYPED_RELS:
        sources = meta["backrefs"].get(pred_uri, [])
        if not sources:
            continue
        items = "".join(
            f'<li><a href="{href(c)}">{label_for(g, c)}</a> {pred_label} this</li>'
            for c in sorted(sources, key=lambda x: label_for(g, x).lower())
        )
        backref_parts.append(
            f'<section><h2>Referenced by</h2><ul>{items}</ul></section>'
        )
    backref_html = "".join(backref_parts)

    return PAGE_TEMPLATE.format(
        title=label,
        breadcrumb=breadcrumb,
        alt_label_html=alt_label_html,
        narrower_html=narrower_html,
        related_html=related_html,
        typed_html=typed_html,
        backref_html=backref_html,
        iri=iri,
        root="",
    )


def main() -> int:
    g = rdflib.Graph()
    g.parse(REPO_ROOT / "ontology" / "loci-ontology.ttl", format="turtle")
    g.parse(REPO_ROOT / "data" / "loci.ttl", format="turtle")

    concepts = collect_concepts(g)

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "concepts").mkdir(parents=True)

    # Find the loci (top concepts under the scheme)
    top = [
        str(c) for c in g.objects(
            None, NS["skos"].hasTopConcept
        )
    ]
    # Fallback: loci are Concepts typed as Locus
    if not top:
        top = [
            str(s) for s in g.subjects(rdflib.RDF.type, NS["loci"].Locus)
        ]

    loci_list = []
    for locus_iri in top:
        meta = concepts[locus_iri]
        children = sorted(meta["narrower"], key=lambda x: label_for(g, x).lower())
        children_html = "".join(
            f'<li><a href="{href(c)}">{label_for(g, c)}</a></li>' for c in children
        )
        loci_list.append(
            f'<li><h2><a href="{href(locus_iri)}">{label_for(g, locus_iri)}</a></h2>'
            f'<p>{len(meta["narrower"])} top-level topics</p>'
            f'<details><summary>Show top-level topics</summary><ul>{children_html}</ul></details>'
            f'</li>'
        )

    (DIST / "index.html").write_text(
        INDEX_TEMPLATE.format(loci_list="".join(loci_list))
    )

    # Per-concept pages
    for iri, meta in concepts.items():
        page = render_page(g, iri, meta)
        (DIST / "concepts" / f"{slug(iri)}.html").write_text(page)

    # Distributable artefacts: also export JSON-LD and a copy of the TTL
    jsonld = g.serialize(format="json-ld", indent=2)
    (DIST / "loci.jsonld").write_text(jsonld)
    ttl = g.serialize(format="turtle")
    (DIST / "loci.ttl").write_text(ttl)
    (DIST / "ontology").mkdir(exist_ok=True)
    shutil.copy(
        REPO_ROOT / "ontology" / "loci-ontology.ttl",
        DIST / "ontology" / "loci-ontology.ttl",
    )

    (DIST / "styles.css").write_text(CSS)

    print(f"Wrote {len(concepts)} concept pages to {DIST}/")
    print(f"  index.html, loci.jsonld, loci.ttl, ontology/, styles.css")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
