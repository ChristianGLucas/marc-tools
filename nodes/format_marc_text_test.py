from gen.messages_pb2 import Field, FormatMarcTextInput, MarcRecord, Subfield
from nodes.format_marc_text import format_marc_text

LEADER = "00000nam a2200000   4500"


def test_format_marc_text_matches_hand_computed_marcmaker_notation(ax):
    """Expected text is computed by hand from the documented MARCMaker
    line grammar (=TAG  IND1IND2$code value..., one line per field, a
    blank-space indicator rendered as a literal backslash) rather than by
    running the node and copying its output.
    """
    record = MarcRecord(
        leader=LEADER,
        fields=[
            Field(tag="001", is_control_field=True, control_value="rec1"),
            Field(
                tag="245",
                is_control_field=False,
                indicator1="0",
                indicator2="0",
                subfields=[Subfield(code="a", value="Title.")],
            ),
        ],
    )

    result = format_marc_text(ax, FormatMarcTextInput(record=record))

    expected = f"=LDR  {LEADER}\n=001  rec1\n=245  00$aTitle.\n"
    assert result.text == expected


def test_format_marc_text_blank_indicators_render_as_backslash(ax):
    """MARCMaker notation renders a blank (space) indicator as a literal
    backslash so it's visible in a fixed-width display -- documented in
    pymarc's own Field.__str__ docstring, citing loc.gov/marc/makrbrkr.html.
    """
    record = MarcRecord(
        leader=LEADER,
        fields=[
            Field(
                tag="500",
                is_control_field=False,
                indicator1=" ",
                indicator2=" ",
                subfields=[Subfield(code="a", value="A general note.")],
            ),
        ],
    )

    result = format_marc_text(ax, FormatMarcTextInput(record=record))

    expected = f"=LDR  {LEADER}\n=500  \\\\$aA general note.\n"
    assert result.text == expected
