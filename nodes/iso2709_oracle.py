# Independent-oracle ISO 2709 codec used ONLY by the test suite.
#
# This is a from-scratch, minimal encoder/decoder for the binary MARC
# (ISO 2709) transmission format, written directly against the format
# spec (https://www.loc.gov/marc/specifications/specrecstruc.html) using
# nothing but stdlib string/byte slicing -- it does NOT import pymarc.
# Its only purpose is to give the tests a correctness oracle that is
# independent of the pymarc library the package itself wraps: encode a
# record here and assert the package's ParseMarc node decodes it to the
# same field/subfield/indicator values, or decode the package's
# SerializeMarc output here and assert it matches what was serialized.
# Round-tripping *through pymarc itself* would only prove self-consistency.
FIELD_TERMINATOR = "\x1e"
SUBFIELD_DELIMITER = "\x1f"
RECORD_TERMINATOR = "\x1d"
LEADER_LEN = 24
DIRECTORY_ENTRY_LEN = 12


def encode_record(fields, record_status="n", type_of_record="a", bibliographic_level="m"):
    """fields: list of either
    ("001", None, None, "control value")                    -- control field
    ("245", "1", "0", [("a", "Title /"), ("c", "Author.")])  -- data field
    Returns the full binary MARC21 record as bytes.
    """
    field_data_chunks = []
    directory_entries = []
    offset = 0
    for tag, ind1, ind2, payload in fields:
        if ind1 is None:
            chunk = payload + FIELD_TERMINATOR
        else:
            subfield_text = "".join(
                f"{SUBFIELD_DELIMITER}{code}{value}" for code, value in payload
            )
            chunk = f"{ind1}{ind2}{subfield_text}{FIELD_TERMINATOR}"
        chunk_bytes = chunk.encode("utf-8")
        field_data_chunks.append(chunk_bytes)
        directory_entries.append(f"{tag:0>3}{len(chunk_bytes):04}{offset:05}")
        offset += len(chunk_bytes)

    directory = ("".join(directory_entries) + FIELD_TERMINATOR).encode("ascii")
    base_address = LEADER_LEN + len(directory)
    field_data = b"".join(field_data_chunks)
    record_length = base_address + len(field_data) + 1  # +1 for RECORD_TERMINATOR

    # Leader positions: 00-04 length, 05 status, 06 type, 07 biblio level,
    # 08 type-of-control, 09 coding scheme ('a'=UTF-8), 10 indicator count,
    # 11 subfield code count, 12-16 base address, 17 encoding level,
    # 18 cataloging form, 19 multipart level, 20-23 entry map "4500".
    leader = (
        f"{record_length:05}{record_status}{type_of_record}{bibliographic_level}"
        f" a22{base_address:05}   4500"
    )
    assert len(leader) == LEADER_LEN, f"internal oracle error: leader len {len(leader)}"

    return leader.encode("ascii") + directory + field_data + RECORD_TERMINATOR.encode("ascii")


def decode_record(data: bytes):
    """Decode a single binary MARC21 record (independent of pymarc).

    Returns (leader_str, [(tag, ind1_or_None, ind2_or_None, payload), ...])
    where payload is a control-field string, or a list of (code, value)
    subfield tuples for a data field.
    """
    leader = data[:LEADER_LEN].decode("ascii")
    base_address = int(leader[12:17])
    directory = data[LEADER_LEN : base_address - 1].decode("ascii")
    assert len(directory) % DIRECTORY_ENTRY_LEN == 0

    fields = []
    for i in range(0, len(directory), DIRECTORY_ENTRY_LEN):
        entry = directory[i : i + DIRECTORY_ENTRY_LEN]
        tag = entry[0:3]
        length = int(entry[3:7])
        start = int(entry[7:12])
        raw = data[base_address + start : base_address + start + length - 1]
        text = raw.decode("utf-8")
        if tag < "010" and tag.isdigit():
            fields.append((tag, None, None, text))
        else:
            ind1, ind2 = text[0], text[1]
            subfield_parts = text[2:].split(SUBFIELD_DELIMITER)[1:]
            subfields = [(part[0], part[1:]) for part in subfield_parts]
            fields.append((tag, ind1, ind2, subfields))
    return leader, fields
