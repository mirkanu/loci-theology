# loci-theology

An open-source hierarchical taxonomy of Christian doctrines, arranged around the traditional **six loci of dogmatics**:

1. **Theology Proper** — the doctrine of God
2. **Anthropology** — the doctrine of man
3. **Christology** — the doctrine of Christ
4. **Soteriology** — the doctrine of salvation
5. **Ecclesiology** — the doctrine of the church
6. **Eschatology** — the doctrine of last things

This is a **taxonomy, not content**. The entry "justification by faith alone" carries a label, a place in the tree, and its cross-relationships to other entries — it does not explain what justification is. Consumers (Bible apps, study tools, recommender systems, theological search) ingest the taxonomy to tag, link, and navigate. Explanations live elsewhere.

## Why this exists

Existing Bible tagging schemes tend to be flat lists, restricted to one tradition, or so coarse they cannot distinguish justification from sanctification. This project aims to be:

- **Deeply hierarchical.** No orphan doctrines: every entry has a parent via `skos:broader`, all the way up to a locus.
- **Cross-linked.** Non-hierarchical relations (`skos:related` plus typed OWL properties) connect an entry under one locus to its counterparts under another — e.g. `human nature of Christ` (Christology) relates to `incarnation` and `atonement` (Soteriology).
- **Reformable.** The taxonomy is data, not a hard-coded tree. Communities fork, merge, and publish their own editions.
- **Machine-readable and human-readable.** Stored as RDF (SKOS + OWL), browsable as a static site, importable as JSON-LD or Turtle.

## Data model

The taxonomy uses three layered W3C standards:

- **[SKOS](https://www.w3.org/TR/skos-reference/)** — the Simple Knowledge Organization System. Concepts, labels (preferred, alternate, hidden), `broader`/`narrower` (hierarchy), `related` (cross-link).
- **[SKOS-XL](https://www.w3.org/TR/skos-reference/skos-xl.html)** — extended labels. Each concept can have a labelled-xL term as its name, so consumers can render `prefLabel` in any language without losing the stable identifier.
- **[OWL 2](https://www.w3.org/TR/owl2-overview/)** — typed relations and class constraints. We declare custom object properties (`dependsOn`, `contrastsWith`, `groundsIn`, `presupposes`) so the taxonomy can express *why* two concepts relate, not just that they do.
- **[SHACL](https://www.w3.org/TR/shacl/)** — Shapes Constraint Language. Validation rules that catch drift: every concept must have exactly one preferred label, must belong to at least one `ConceptScheme`, must have a broader concept unless it is a top-level locus.

The canonical file is [`data/loci.ttl`](data/loci.ttl) (Turtle). The build step emits a JSON-LD copy for web consumption.

### Concept sketch

```turtle
ex:humanNatureOfChrist a skos:Concept ;
    skos:prefLabel "Human Nature of Christ"@en ;
    skos:altLabel "Christ's Humanity"@en ;
    skos:broader ex:naturesOfChrist ;
    skos:related ex:atonement , ex:incarnation ;
    dcterms:isPartOf ex:schemeChristology ;
    ex:groundsIn ex:divineNatureOfChrist .
```

## Repository layout

```
.
├── data/
│   ├── loci.ttl              # canonical taxonomy (Turtle / SKOS+OWL)
│   ├── loci.jsonld           # build artefact: same data as JSON-LD
│   └── shapes.ttl            # SHACL validation shapes
├── docs/                     # GitHub Pages site (static browse UI)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── src/
│   └── build.js              # turtle → jsonld + html pages
├── ontology/
│   └── loci-ontology.ttl     # our typed OWL properties and classes
├── README.md
├── CONTRIBUTING.md
├── LICENSE                   # MIT
└── AGENTS.md                 # workflow notes for AI coding agents
```

## Getting started

Browse the taxonomy: <https://mirkanu.github.io/loci-theology/>

To validate locally (requires `pip install pyshacl rdflib`):

```bash
python tools/validate.py data/loci.ttl
```

To build the site:

```bash
node src/build.js
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: open an issue proposing new concepts or new typed relations; PRs that add or restructure concepts are welcome once the issue is agreed. We do **not** add explanatory content here — only labels, hierarchy, and relations.

## License

MIT. See [`LICENSE`](LICENSE).
