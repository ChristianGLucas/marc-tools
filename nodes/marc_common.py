# Shared helpers for the marc-tools package: canonical MarcRecord <-> pymarc.Record
# conversion, per-format parse/serialize dispatch, and input-size/count bounds.
#
# Security note: pymarc's JSONReader treats a bare string argument as a
# candidate *filesystem path* (via os.path.exists) before falling back to
# treating it as JSON text, and xml.sax's parser.parse() treats a bare
# string argument as a filename/URI. Both of those constructors are only
# ever called here wrapped in an io.StringIO/io.BytesIO, which both
# libraries special-case as an in-memory stream *before* any path/URI
# handling -- this is intentional and must not be "simplified" back to
# passing raw text, or a caller-controlled string could trigger a local
# file read.
import io

import pymarc
from gen.messages_pb2 import Field as FieldMsg
from gen.messages_pb2 import MarcFormat
from gen.messages_pb2 import MarcRecord as MarcRecordMsg
from gen.messages_pb2 import Subfield as SubfieldMsg

# Bounds on untrusted input, enforced before any parse work begins.
MAX_INPUT_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_RECORDS = 5000
LEADER_LEN = 24


class MarcToolsError(Exception):
    """Raised for any structured, caller-facing error condition."""


def check_input_size(data: bytes) -> None:
    if len(data) > MAX_INPUT_BYTES:
        raise MarcToolsError(
            f"input exceeds the {MAX_INPUT_BYTES}-byte limit ({len(data)} bytes)"
        )


def check_record_count(records: list) -> None:
    if len(records) > MAX_RECORDS:
        raise MarcToolsError(
            f"input exceeds the {MAX_RECORDS}-record limit ({len(records)} records)"
        )


def pymarc_field_to_message(field: pymarc.Field) -> FieldMsg:
    if field.control_field:
        return FieldMsg(
            tag=field.tag,
            is_control_field=True,
            control_value=field.data or "",
        )
    subfields = [SubfieldMsg(code=sf.code, value=sf.value) for sf in field.subfields]
    return FieldMsg(
        tag=field.tag,
        is_control_field=False,
        indicator1=field.indicator1 or " ",
        indicator2=field.indicator2 or " ",
        subfields=subfields,
    )


def pymarc_record_to_message(record: "pymarc.Record") -> MarcRecordMsg:
    return MarcRecordMsg(
        leader=str(record.leader),
        fields=[pymarc_field_to_message(f) for f in record.fields],
    )


def message_field_to_pymarc(field_msg: FieldMsg) -> pymarc.Field:
    if field_msg.is_control_field:
        return pymarc.Field(tag=field_msg.tag, data=field_msg.control_value)
    subfields = [
        pymarc.Subfield(code=sf.code, value=sf.value) for sf in field_msg.subfields
    ]
    ind1 = field_msg.indicator1 or " "
    ind2 = field_msg.indicator2 or " "
    return pymarc.Field(
        tag=field_msg.tag,
        indicators=pymarc.Indicators(ind1, ind2),
        subfields=subfields,
    )


def message_to_pymarc_record(record_msg: MarcRecordMsg) -> pymarc.Record:
    leader = record_msg.leader or " " * LEADER_LEN
    if len(leader) != LEADER_LEN:
        # Be forgiving of a short/long leader from a hand-built envelope --
        # pymarc.Leader requires exactly 24 chars -- pad or truncate rather
        # than crash; ValidateMarcRecord is the node that judges strictness.
        leader = (leader + " " * LEADER_LEN)[:LEADER_LEN]
    fields = [message_field_to_pymarc(f) for f in record_msg.fields]
    return pymarc.Record(leader=leader, fields=fields)


def parse_records(data: bytes, fmt: int) -> list:
    """Parse `data` in the given MarcFormat into a list of pymarc.Record.

    Always wraps content in an in-memory stream before handing it to a
    pymarc reader -- see the module docstring for why that isn't optional.
    """
    check_input_size(data)

    if fmt == MarcFormat.MARC_FORMAT_MARC21:
        reader = pymarc.MARCReader(io.BytesIO(data), to_unicode=True)
        records = []
        for index, record in enumerate(reader):
            if record is None:
                raise MarcToolsError(
                    f"malformed MARC21 record at index {index}: {reader.current_exception}"
                )
            records.append(record)
        if not records:
            raise MarcToolsError("no MARC21 records found in input")
        check_record_count(records)
        return records

    if fmt == MarcFormat.MARC_FORMAT_MARCXML:
        text = _decode_text(data)
        try:
            records = pymarc.parse_xml_to_array(io.StringIO(text))
        except Exception as exc:  # noqa: BLE001 - surfaced as a structured error
            raise MarcToolsError(f"malformed MARCXML input: {exc}") from exc
        if not records:
            raise MarcToolsError("no MARC records found in MARCXML input")
        check_record_count(records)
        return records

    if fmt == MarcFormat.MARC_FORMAT_MARC_IN_JSON:
        text = _decode_text(data)
        try:
            records = pymarc.parse_json_to_array(io.StringIO(text))
        except Exception as exc:  # noqa: BLE001 - surfaced as a structured error
            raise MarcToolsError(f"malformed MARC-in-JSON input: {exc}") from exc
        if not records:
            raise MarcToolsError("no MARC records found in MARC-in-JSON input")
        check_record_count(records)
        return records

    raise MarcToolsError(f"unrecognized or unspecified MarcFormat: {fmt}")


def serialize_records(records: list, fmt: int) -> bytes:
    if not records:
        raise MarcToolsError("no records to serialize")
    check_record_count(records)

    if fmt == MarcFormat.MARC_FORMAT_MARC21:
        return b"".join(record.as_marc() for record in records)

    if fmt == MarcFormat.MARC_FORMAT_MARCXML:
        out = io.BytesIO()
        writer = pymarc.XMLWriter(out)
        for record in records:
            writer.write(record)
        writer.close(close_fh=False)
        return out.getvalue()

    if fmt == MarcFormat.MARC_FORMAT_MARC_IN_JSON:
        out = io.StringIO()
        writer = pymarc.JSONWriter(out)
        for record in records:
            writer.write(record)
        writer.close(close_fh=False)
        return out.getvalue().encode("utf-8")

    raise MarcToolsError(f"unrecognized or unspecified MarcFormat: {fmt}")


def _decode_text(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MarcToolsError(f"input is not valid UTF-8 text: {exc}") from exc
    if len(text) > MAX_INPUT_BYTES:
        raise MarcToolsError(
            f"input exceeds the {MAX_INPUT_BYTES}-character limit ({len(text)} chars)"
        )
    return text


def format_field_value(field: pymarc.Field) -> str:
    """Human-friendly rendering of one field's content (control value or
    space-joined subfield values), used by ExtractBibliographicEntities.
    """
    return field.format_field() if not field.control_field else (field.data or "")
