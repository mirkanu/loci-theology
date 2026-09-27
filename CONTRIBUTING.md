# Contributing

Thanks for helping build a shared taxonomy of Christian doctrine.

## What belongs here

Only **labels, hierarchy, and relationships**. No definitions, no commentary, no exegesis. If you want to write a doctrinal article, link to it from a `skos:related` entry — do not embed it.

## Workflow

1. **Open an issue first.** Even for a single new concept. The shape of the taxonomy is a community decision, not a unilateral edit. Use the issue template; say which locus, what broader concept it sits under, and which concepts it should relate to.
2. **Use the SKOS/OWL vocabulary in `ontology/`.** Don't invent ad-hoc predicates.
3. **Add a SHACL rule** if you introduce a new constraint (e.g. "every Soteriological concept must relate to at least one Christological concept"). Update `data/shapes.ttl` and the CI validator.
4. **Validate locally** before pushing:
   ```bash
   python tools/validate.py data/loci.ttl
   ```
5. **Open a PR.** Reference the issue (`Closes #N`). The build artefact and Pages site will regenerate on merge to `main`.

## Style

- **Labels are Title Case**, English. Add `altLabel` for common variants (e.g. `Justification by Faith` as alt for `Justification by Faith Alone`).
- **Concept IDs are stable.** Once a concept has an `ex:` identifier, never rename it. Rename labels freely; rename IDs only via a deliberate migration.
- **Hierarchy is shallow where possible.** If a chain goes four levels deep, question whether the middle concepts earn their place.
- **Cross-links are typed.** Prefer `ex:groundsIn`, `ex:contrastsWith`, `ex:dependsOn` over the generic `skos:related`.

## What we won't merge

- Doctrinal advocacy dressed as taxonomy (e.g. one tradition's polemic encoded as "this concept supersedes that one").
- Long altLabels or prefLabels. Keep them under ~40 characters.
- Concepts without a `broader` parent unless they are one of the six loci.
