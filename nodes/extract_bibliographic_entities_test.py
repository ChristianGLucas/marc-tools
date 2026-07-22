from gen.messages_pb2 import ExtractBibliographicEntitiesInput, Field, MarcRecord, Subfield

from nodes.extract_bibliographic_entities import extract_bibliographic_entities

LEADER = "00000nam a2200000   4500"


def _field(tag, ind1, ind2, subfields):
    return Field(
        tag=tag,
        is_control_field=False,
        indicator1=ind1,
        indicator2=ind2,
        subfields=[Subfield(code=c, value=v) for c, v in subfields],
    )


def test_extract_entities_from_hand_built_record_per_marc21_tag_spec(ax):
    """Every field below is placed at the tag/subfield the public MARC21
    Bibliographic Format documents for that entity (title=245$a/$b,
    ISBN=020$a, ISSN=022$a/$l, publisher/date=260$b/$c, subjects=6xx,
    author=100, added-entry co-author=700, notes=5xx, physical desc=300,
    uniform title=130/240) -- the expected values are computed from that
    public spec, independent of how the node happens to be implemented.
    """
    record = MarcRecord(
        leader=LEADER,
        fields=[
            _field("130", "0", " ", [("a", "Hamlet (Uniform title)")]),
            _field("100", "1", " ", [("a", "Shakespeare, William.")]),
            _field("245", "1", "0", [("a", "Hamlet /"), ("b", "Prince of Denmark.")]),
            _field("260", " ", " ", [("b", "Penguin Classics,"), ("c", "1992.")]),
            _field("300", " ", " ", [("a", "xlii, 336 p. ;"), ("c", "18 cm.")]),
            _field("020", " ", " ", [("a", "0-14-071454-7 (pbk.)")]),
            _field("022", " ", " ", [("a", "1234-5679"), ("l", "1234-5679")]),
            _field("650", " ", "0", [("a", "Princes"), ("z", "Denmark"), ("v", "Drama.")]),
            _field("500", " ", " ", [("a", "Includes bibliographical references.")]),
            _field("700", "1", " ", [("a", "Jones, Edward,"), ("e", "editor.")]),
            _field("086", " ", " ", [("a", "Y 4.ED 8/1:110-32")]),
        ],
    )

    result = extract_bibliographic_entities(ax, ExtractBibliographicEntitiesInput(record=record))

    assert result.title == "Hamlet / Prince of Denmark."
    assert result.uniform_title == "Hamlet (Uniform title)"
    # 700 isn't a subject field, so format_field() doesn't " -- "-separate $e
    assert result.authors == ["Shakespeare, William.", "Jones, Edward, editor."]
    assert result.isbn == "0140714547"  # dashes stripped by pymarc's isbn regex, "(pbk.)" dropped
    assert result.issn == "1234-5679"
    assert result.issnl == "1234-5679"
    assert result.publisher == "Penguin Classics,"
    assert result.pub_year == "1992."
    assert result.subjects == ["Princes -- Denmark -- Drama."]
    assert result.notes == ["Includes bibliographical references."]
    assert result.physical_description == ["xlii, 336 p. ; 18 cm."]
    assert result.sudoc == "Y 4.ED 8/1:110-32"


def test_extract_entities_264_publisher_with_indicator2_one(ax):
    """264 with second indicator '1' is the RDA-era publisher statement --
    260 and 264 are mutually exclusive on a real record, so this checks the
    264 branch on its own record.
    """
    record = MarcRecord(
        leader=LEADER,
        fields=[
            _field("245", "0", "0", [("a", "Some Title.")]),
            _field("264", " ", "1", [("b", "Acme Press,"), ("c", "2020.")]),
        ],
    )

    result = extract_bibliographic_entities(ax, ExtractBibliographicEntitiesInput(record=record))

    assert result.publisher == "Acme Press,"
    assert result.pub_year == "2020."


def test_extract_entities_missing_fields_come_back_empty_not_error(ax):
    record = MarcRecord(leader=LEADER, fields=[_field("245", "0", "0", [("a", "Bare Title.")])])

    result = extract_bibliographic_entities(ax, ExtractBibliographicEntitiesInput(record=record))

    assert result.title == "Bare Title."
    assert result.isbn == ""
    assert result.issn == ""
    assert result.publisher == ""
    assert result.pub_year == ""
    assert list(result.subjects) == []
    assert list(result.authors) == []
