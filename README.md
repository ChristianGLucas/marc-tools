# marc-tools

Composable [Axiom](https://axiomide.com) nodes for **MARC bibliographic /
library-catalog records** — parsing, serializing, validating, and extracting
higher-level bibliographic entities from MARC21 and UNIMARC records, in
binary MARC (ISO 2709), MARCXML, or MARC-in-JSON.

Built for the Axiom marketplace (handle `christiangeorgelucas`). Wraps
[pymarc](https://gitlab.com/pymarc/pymarc) (BSD-2-Clause, zero transitive
dependencies), the standard Python library for reading, writing, and
modifying MARC records, used across the library-science/code4lib community.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/marc-tools@0.1.0

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/marc-tools/ParseMarc --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/marc-tools/0.1.0/ParseMarc \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/marc-tools/ParseMarc`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

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
