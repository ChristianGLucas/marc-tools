from gen.axiom_context import AxiomContext
from gen.messages_pb2 import ParseMarcInput, ParseMarcOutput
from nodes.marc_common import MarcToolsError, parse_records, pymarc_record_to_message


def parse_marc(ax: AxiomContext, input: ParseMarcInput) -> ParseMarcOutput:
    """Parse one or more MARC bibliographic/authority/holdings records from
    binary MARC21 (ISO 2709), MARCXML, or MARC-in-JSON into the package's
    canonical MarcRecord envelope. Malformed input, an unrecognized format,
    or oversized input returns a structured error instead of raising.
    """
    try:
        records = parse_records(input.data, input.format)
    except MarcToolsError as exc:
        return ParseMarcOutput(error=True, error_message=str(exc))

    messages = [pymarc_record_to_message(record) for record in records]
    return ParseMarcOutput(records=messages, count=len(messages))
