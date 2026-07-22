from gen.messages_pb2 import MarcFormat, ValidateMarcRecordInput
from nodes.iso2709_oracle import encode_record
from nodes.validate_marc_record import validate_marc_record

GOOD_FIELDS = [
    ("001", None, None, "valrec1"),
    ("245", "0", "0", [("a", "Valid Record.")]),
]


def test_validate_well_formed_marc21_is_valid(ax):
    data = encode_record(GOOD_FIELDS)
    result = validate_marc_record(
        ax, ValidateMarcRecordInput(data=data, format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.valid is True
    assert list(result.errors) == []
    assert result.record_count == 1


def test_validate_two_well_formed_marc21_records(ax):
    data = encode_record(GOOD_FIELDS) + encode_record(GOOD_FIELDS)
    result = validate_marc_record(
        ax, ValidateMarcRecordInput(data=data, format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.valid is True
    assert result.record_count == 2


def test_validate_truncated_marc21_is_invalid(ax):
    data = encode_record(GOOD_FIELDS)[:10]  # chop off mid-directory
    result = validate_marc_record(
        ax, ValidateMarcRecordInput(data=data, format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.valid is False
    assert len(result.errors) >= 1


def test_validate_bad_record_length_prefix_is_invalid(ax):
    data = bytearray(encode_record(GOOD_FIELDS))
    data[0:5] = b"XXXXX"  # record length must be numeric
    result = validate_marc_record(
        ax, ValidateMarcRecordInput(data=bytes(data), format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.valid is False
    assert len(result.errors) >= 1


def test_validate_well_formed_marcxml_is_valid(ax):
    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<collection xmlns="http://www.loc.gov/MARC21/slim">'
        b"<record>"
        b'<leader>00000nam a2200000   4500</leader>'
        b'<controlfield tag="001">xmlrec1</controlfield>'
        b"</record>"
        b"</collection>"
    )
    result = validate_marc_record(
        ax, ValidateMarcRecordInput(data=xml, format=MarcFormat.MARC_FORMAT_MARCXML)
    )
    assert result.valid is True
    assert result.record_count == 1


def test_validate_malformed_marcxml_is_invalid(ax):
    result = validate_marc_record(
        ax,
        ValidateMarcRecordInput(data=b"<not><xml", format=MarcFormat.MARC_FORMAT_MARCXML),
    )
    assert result.valid is False
    assert len(result.errors) >= 1


def test_validate_oversized_input_is_invalid(ax):
    from nodes.marc_common import MAX_INPUT_BYTES

    oversized = b"0" * (MAX_INPUT_BYTES + 1)
    result = validate_marc_record(
        ax, ValidateMarcRecordInput(data=oversized, format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.valid is False
    assert "byte limit" in result.errors[0]
