import json

from gen.messages_pb2 import Field, MarcFormat, MarcRecord, SerializeMarcInput, Subfield
from nodes.iso2709_oracle import decode_record
from nodes.serialize_marc import serialize_marc

LEADER = "00000nam a2200000   4500"


def _hand_built_record():
    return MarcRecord(
        leader=LEADER,
        fields=[
            Field(tag="001", is_control_field=True, control_value="handbuilt1"),
            Field(
                tag="245",
                is_control_field=False,
                indicator1="1",
                indicator2="0",
                subfields=[Subfield(code="a", value="Hand-Built Title /")],
            ),
        ],
    )


def test_serialize_marc21_matches_independent_iso2709_oracle(ax):
    """Decodes SerializeMarc's binary output with the from-scratch
    ISO 2709 decoder (nodes/iso2709_oracle.py, no pymarc involved) rather
    than pymarc itself, so the check is independent of the encoder.
    """
    record = _hand_built_record()
    result = serialize_marc(
        ax, SerializeMarcInput(records=[record], format=MarcFormat.MARC_FORMAT_MARC21)
    )

    assert result.error is False
    leader, fields = decode_record(result.data)
    assert leader[6] == "a"  # type_of_record from LEADER
    assert fields[0] == ("001", None, None, "handbuilt1")
    assert fields[1][0] == "245"
    assert fields[1][1] == "1" and fields[1][2] == "0"
    assert fields[1][3] == [("a", "Hand-Built Title /")]


def test_serialize_marcxml_parses_with_stdlib_elementtree(ax):
    """Parses SerializeMarc's MARCXML output with Python's own
    xml.etree.ElementTree directly, independent of pymarc's XML handling.
    """
    import xml.etree.ElementTree as ET

    record = _hand_built_record()
    result = serialize_marc(
        ax, SerializeMarcInput(records=[record], format=MarcFormat.MARC_FORMAT_MARCXML)
    )

    assert result.error is False
    ns = {"m": "http://www.loc.gov/MARC21/slim"}
    root = ET.fromstring(result.data)
    record_el = root.find("m:record", ns)
    assert record_el is not None
    control_el = record_el.find('m:controlfield[@tag="001"]', ns)
    assert control_el.text == "handbuilt1"
    data_el = record_el.find('m:datafield[@tag="245"]', ns)
    assert data_el.attrib["ind1"] == "1"
    subfield_el = data_el.find('m:subfield[@code="a"]', ns)
    assert subfield_el.text == "Hand-Built Title /"


def test_serialize_marc_in_json_parses_with_stdlib_json(ax):
    record = _hand_built_record()
    result = serialize_marc(
        ax, SerializeMarcInput(records=[record], format=MarcFormat.MARC_FORMAT_MARC_IN_JSON)
    )

    assert result.error is False
    parsed = json.loads(result.data)
    assert isinstance(parsed, list)
    assert parsed[0]["leader"] == LEADER
    assert parsed[0]["fields"][0] == {"001": "handbuilt1"}
    assert parsed[0]["fields"][1]["245"]["ind1"] == "1"
    assert parsed[0]["fields"][1]["245"]["subfields"] == [{"a": "Hand-Built Title /"}]


def test_serialize_marc_empty_records_returns_structured_error(ax):
    result = serialize_marc(
        ax, SerializeMarcInput(records=[], format=MarcFormat.MARC_FORMAT_MARC21)
    )
    assert result.error is True
    assert result.error_message


def test_serialize_marc_unspecified_format_returns_structured_error(ax):
    record = _hand_built_record()
    result = serialize_marc(
        ax, SerializeMarcInput(records=[record], format=MarcFormat.MARC_FORMAT_UNSPECIFIED)
    )
    assert result.error is True
