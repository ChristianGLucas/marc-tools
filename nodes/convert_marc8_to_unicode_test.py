from gen.messages_pb2 import ConvertMarc8Input
from nodes.convert_marc8_to_unicode import MAX_MARC8_BYTES, convert_marc8_to_unicode


def test_convert_marc8_grave_accent_matches_loc_ansel_table(ax):
    """0xE1 is the ANSEL "combining grave accent" escape in the LC MARC-8
    character set table (see loc.gov/marc/specifications/speccharmarc8.html)
    and precedes its base letter in MARC-8, unlike Unicode's own combining
    marks which follow the base letter. LC's own documented mapping is the
    oracle here: byte sequence \\xe1 + 'a' is independently known (from
    the published ANSEL table, not from running this code) to represent
    the precomposed character U+00E0 LATIN SMALL LETTER A WITH GRAVE ("à").
    """
    result = convert_marc8_to_unicode(
        ax, ConvertMarc8Input(marc8_data=bytes([0xE1]) + b"a")
    )
    assert result.error is False
    assert result.unicode_text == "à"  # "à"


def test_convert_marc8_plain_ascii_is_passthrough(ax):
    result = convert_marc8_to_unicode(ax, ConvertMarc8Input(marc8_data=b"Effective Java"))
    assert result.error is False
    assert result.unicode_text == "Effective Java"


def test_convert_marc8_empty_input_is_empty_string(ax):
    result = convert_marc8_to_unicode(ax, ConvertMarc8Input(marc8_data=b""))
    assert result.error is False
    assert result.unicode_text == ""


def test_convert_marc8_oversized_input_returns_structured_error(ax):
    oversized = b"a" * (MAX_MARC8_BYTES + 1)
    result = convert_marc8_to_unicode(ax, ConvertMarc8Input(marc8_data=oversized))
    assert result.error is True
    assert "byte limit" in result.error_message
