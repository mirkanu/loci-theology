#!/usr/bin/env python3
"""Validate data/loci.ttl against data/shapes.ttl using SHACL.

Exit code 0 means valid, 1 means SHACL violations found.

Usage:
    python tools/validate.py
    python tools/validate.py path/to/data.ttl
"""
from __future__ import annotations

import sys
from pathlib import Path

import rdflib
import pyshacl

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    data_file = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "data" / "loci.ttl"
    shapes_file = REPO_ROOT / "data" / "shapes.ttl"
    ontology_file = REPO_ROOT / "ontology" / "loci-ontology.ttl"

    g = rdflib.Graph()
    g.parse(ontology_file, format="turtle")
    g.parse(data_file, format="turtle")
    sg = rdflib.Graph()
    sg.parse(shapes_file, format="turtle")

    conforms, _, results_text = pyshacl.validate(
        g,
        shacl_graph=sg,
        meta_shacl=False,
        debug=False,
        inference="rdfs",
    )

    print(f"Loaded {len(g)} triples from {ontology_file} + {data_file}")
    print(f"SHACL conforms: {conforms}")
    if not conforms:
        print(results_text)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
