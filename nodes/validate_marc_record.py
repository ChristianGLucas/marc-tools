import io

import pymarc
from gen.axiom_context import AxiomContext
from gen.messages_pb2 import MarcFormat, ValidateMarcRecordInput, ValidateMarcRecordOutput
from nodes.marc_common import MarcToolsError, parse_records


def validate_marc_record(ax: AxiomContext, input: ValidateMarcRecordInput) -> ValidateMarcRecordOutput:
    """Structurally validate one or more MARC records in binary MARC21,
    MARCXML, or MARC-in-JSON without needing them pre-parsed -- checks the
    24-byte leader, the directory's byte-offset consistency, and
    record-length/base-address bounds (binary), or that the document parses
    into at least one well-formed record (MARCXML/JSON). Returns valid=false
    with one structured error message per problem found rather than raising;
    a well-formed empty document is valid with record_count 0.
    """
    data = input.data
    fmt = input.format

    if fmt == MarcFormat.MARC_FORMAT_MARC21:
        errors = []
        record_count = 0
        try:
            reader = pymarc.MARCReader(io.BytesIO(data), to_unicode=True)
            for index, record in enumerate(reader):
                if record is None:
                    errors.append(f"record at index {index}: {reader.current_exception}")
                else:
                    record_count += 1
        except Exception as exc:  # noqa: BLE001 - surfaced as a structured error
            errors.append(f"fatal read error: {exc}")
        if record_count == 0 and not errors:
            errors.append("no MARC21 records found in input")
        return ValidateMarcRecordOutput(
            valid=(len(errors) == 0), errors=errors, record_count=record_count
        )

    if fmt in (MarcFormat.MARC_FORMAT_MARCXML, MarcFormat.MARC_FORMAT_MARC_IN_JSON):
        try:
            records = parse_records(data, fmt)
        except MarcToolsError as exc:
            return ValidateMarcRecordOutput(valid=False, errors=[str(exc)], record_count=0)
        return ValidateMarcRecordOutput(valid=True, errors=[], record_count=len(records))

    return ValidateMarcRecordOutput(
        valid=False,
        errors=[f"unrecognized or unspecified MarcFormat: {fmt}"],
        record_count=0,
    )
