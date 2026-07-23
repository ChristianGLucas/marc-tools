# marc-tools

Composable [Axiom](https://axiomide.com) nodes for **MARC bibliographic /
library-catalog records** — parsing, serializing, validating, and extracting
higher-level bibliographic entities from MARC21 and UNIMARC records, in
binary MARC (ISO 2709), MARCXML, or MARC-in-JSON.

Built for the Axiom marketplace (handle `christiangeorgelucas`). Wraps
[pymarc](https://gitlab.com/pymarc/pymarc) (BSD-2-Clause, zero transitive
dependencies), the standard Python library for reading, writing, and
modifying MARC records, used across the library-science/code4lib community.

## Nodes

- **ParseMarc** — decode binary MARC21, MARCXML, or MARC-in-JSON into the
  package's canonical `MarcRecord` envelope (leader + ordered fields).
- **SerializeMarc** — render a `MarcRecord` back into binary MARC21, MARCXML,
  or MARC-in-JSON.
- **ParseLeader** — decode a raw 24-character MARC leader into its
  fixed-position structural fields.
- **ExtractBibliographicEntities** — pull title, author(s), ISBN/ISSN,
  publisher/date, subjects, series, notes, physical description, and SuDoc
  number out of a `MarcRecord`, using standard MARC21 tag conventions.
- **ValidateMarcRecord** — structurally validate MARC21/MARCXML/MARC-in-JSON
  input without a separate parse step.
- **ConvertMarc8ToUnicode** — convert legacy MARC-8 (ANSI/NISO Z39.47)
  encoded bytes to Unicode text.
- **FormatMarcText** — render a `MarcRecord` as a human-readable MARCMaker
  "staff view" (`=245  10$aTitle ...`).

`ParseMarc`/`SerializeMarc`/`ParseLeader`/`ValidateMarcRecord` operate on the
raw ISO 2709 binary structure and the MARCXML container schema, both of
which are shared by MARC21 and UNIMARC records; `ExtractBibliographicEntities`
uses MARC21-specific tag conventions.

Stateless, offline (no network calls, no external service), deterministic,
with hard size/record-count bounds on untrusted input and structured errors
instead of crashes.

## License

MIT. See [LICENSE](LICENSE).
