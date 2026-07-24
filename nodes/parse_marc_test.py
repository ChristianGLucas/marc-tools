from gen.messages_pb2 import MarcFormat, ParseMarcInput
from nodes.iso2709_oracle import encode_record
from nodes.parse_marc import parse_marc

ORACLE_FIELDS = [
    ("001", None, None, "ocm12345"),
    ("020", " ", " ", [("a", "9780134685991")]),
    ("100", "1", " ", [("a", "Bloch, Joshua.")]),
    ("245", "1", "0", [("a", "Effective Java /"), ("c", "Joshua Bloch.")]),
    ("650", " ", "0", [("a", "Java (Computer program language)")]),
]


def test_parse_marc21_matches_independent_iso2709_oracle(ax):
    """Cross-checks ParseMarc's decode against a hand-written, from-scratch
    ISO 2709 encoder (nodes/iso2709_oracle.py) that does not import pymarc --
    a self-round-trip through pymarc alone would only prove self-consistency.
    """
    data = encode_record(ORACLE_FIELDS)
    result = parse_marc(ax, ParseMarcInput(data=data, format=MarcFormat.MARC_FORMAT_MARC21))

    assert result.error is False
    assert result.count == 1
    record = result.records[0]
    assert len(record.leader) == 24
    assert record.leader[5] == "n"  # record_status set by the oracle encoder

    control = record.fields[0]
    assert control.tag == "001"
    assert control.is_control_field is True
    assert control.control_value == "ocm12345"

    isbn_field = record.fields[1]
    assert isbn_field.tag == "020"
    assert isbn_field.is_control_field is False
    assert [(s.code, s.value) for s in isbn_field.subfields] == [("a", "9780134685991")]

    title_field = record.fields[3]
    assert title_field.tag == "245"
    assert title_field.indicator1 == "1"
    assert title_field.indicator2 == "0"
    assert [(s.code, s.value) for s in title_field.subfields] == [
        ("a", "Effective Java /"),
        ("c", "Joshua Bloch."),
    ]


def test_parse_marc21_multiple_records(ax):
    one = encode_record([("001", None, None, "rec-1"), ("245", "0", "0", [("a", "First.")])])
    two = encode_record([("001", None, None, "rec-2"), ("245", "0", "0", [("a", "Second.")])])
    result = parse_marc(ax, ParseMarcInput(data=one + two, format=MarcFormat.MARC_FORMAT_MARC21))

    assert result.error is False
    assert result.count == 2
    assert result.records[0].fields[0].control_value == "rec-1"
    assert result.records[1].fields[0].control_value == "rec-2"


def test_parse_marcxml(ax):
    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<collection xmlns="http://www.loc.gov/MARC21/slim">'
        b"<record>"
        b'<leader>00000nam a2200000   4500</leader>'
        b'<controlfield tag="001">xmlrec1</controlfield>'
        b'<datafield tag="245" ind1="0" ind2="0">'
        b'<subfield code="a">XML Title.</subfield>'
        b"</datafield>"
        b"</record>"
        b"</collection>"
    )
    result = parse_marc(ax, ParseMarcInput(data=xml, format=MarcFormat.MARC_FORMAT_MARCXML))

    assert result.error is False
    assert result.count == 1
    record = result.records[0]
    assert record.fields[0].control_value == "xmlrec1"
    assert record.fields[1].tag == "245"
    assert record.fields[1].subfields[0].value == "XML Title."


def test_parse_marc_in_json(ax):
    json_text = (
        b'{"leader":"00000nam a2200000   4500","fields":['
        b'{"001":"jsonrec1"},'
        b'{"245":{"ind1":"0","ind2":"0","subfields":[{"a":"JSON Title."}]}}'
        b"]}"
    )
    result = parse_marc(
        ax, ParseMarcInput(data=json_text, format=MarcFormat.MARC_FORMAT_MARC_IN_JSON)
    )

    assert result.error is False
    assert result.count == 1
    record = result.records[0]
    assert record.fields[0].control_value == "jsonrec1"
    assert record.fields[1].subfields[0].value == "JSON Title."


def test_parse_marc21_malformed_returns_structured_error(ax):
    result = parse_marc(
        ax, ParseMarcInput(data=b"not a marc record", format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.error is True
    assert result.error_message
    assert result.count == 0


def test_parse_marc_unspecified_format_returns_structured_error(ax):
    data = encode_record(ORACLE_FIELDS)
    result = parse_marc(ax, ParseMarcInput(data=data, format=MarcFormat.MARC_FORMAT_UNSPECIFIED))
    assert result.error is True
    assert "format" in result.error_message.lower()


def test_parse_marc21_large_malformed_input_does_not_crash(ax):
    # No payload-size limit is imposed by this node -- the platform bounds
    # that, not the node. A large, malformed (not real MARC21) input still
    # surfaces as a structured error rather than an unhandled crash.
    large = b"0" * 2_000_001
    result = parse_marc(ax, ParseMarcInput(data=large, format=MarcFormat.MARC_FORMAT_MARC21))
    assert result.error is True
    assert result.error_message
    assert result.count == 0
