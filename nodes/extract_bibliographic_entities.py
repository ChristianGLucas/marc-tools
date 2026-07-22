from gen.axiom_context import AxiomContext
from gen.messages_pb2 import BibliographicEntities, ExtractBibliographicEntitiesInput
from nodes.marc_common import format_field_value, message_to_pymarc_record

# Added-entry tags treated as co-author/contributor names (personal,
# corporate, and meeting name added entries) -- 730/740 and the local
# 75x-79x ranges are uniform-title / other added entries, not authors.
AUTHOR_ADDED_ENTRY_TAGS = {"700", "710", "711", "720"}


def extract_bibliographic_entities(ax: AxiomContext, input: ExtractBibliographicEntitiesInput) -> BibliographicEntities:
    """Extract higher-level bibliographic entities from a MarcRecord using
    standard MARC21 tag conventions -- title (245), uniform title (130/240),
    main/added-entry authors (100/110/111/700/710/711/720), ISBN (020), ISSN
    and ISSN-L (022), publisher and publication year (260/264), subjects
    (6xx), series (4xx/8xx), notes (5xx), physical description (300), and
    SuDoc number (086). A field the record does not carry comes back as an
    empty string or empty list, never an error -- extraction is best-effort
    over whatever tags are present.
    """
    record = message_to_pymarc_record(input.record)

    authors = []
    main_author = record.author
    if main_author:
        authors.append(main_author)
    for field in record.addedentries:
        if field.tag in AUTHOR_ADDED_ENTRY_TAGS:
            authors.append(format_field_value(field))

    return BibliographicEntities(
        title=record.title or "",
        uniform_title=record.uniformtitle or "",
        authors=authors,
        isbn=record.isbn or "",
        issn=record.issn or "",
        issnl=record.issnl or "",
        publisher=record.publisher or "",
        pub_year=record.pubyear or "",
        subjects=[format_field_value(f) for f in record.subjects],
        series=[format_field_value(f) for f in record.series],
        notes=[format_field_value(f) for f in record.notes],
        physical_description=[format_field_value(f) for f in record.physicaldescription],
        sudoc=record.sudoc or "",
    )
