import pymarc
from gen.axiom_context import AxiomContext
from gen.messages_pb2 import LeaderFields, ParseLeaderInput
from pymarc.exceptions import RecordLeaderInvalid

LEADER_LEN = 24


def _to_int(value: str, field_name: str) -> int:
    if not value.isdigit():
        raise ValueError(f"{field_name} is not numeric: {value!r}")
    return int(value)


def parse_leader(ax: AxiomContext, input: ParseLeaderInput) -> LeaderFields:
    """Decode a raw 24-character MARC leader string into its fixed-position
    structural fields. The leader's physical layout is shared by MARC21 and
    UNIMARC binary records, so this works for either. A leader that is not
    exactly 24 characters, or has a non-numeric record-length/base-address,
    returns a structured error instead of raising.
    """
    raw = input.leader
    if len(raw) != LEADER_LEN:
        return LeaderFields(
            error=True,
            error_message=f"leader must be exactly {LEADER_LEN} characters, got {len(raw)}",
        )

    try:
        leader = pymarc.Leader(raw)
        record_length = _to_int(leader.record_length, "record length (positions 00-04)")
        base_address = _to_int(leader.base_address, "base address of data (positions 12-16)")
        indicator_count = _to_int(leader.indicator_count, "indicator count (position 10)")
        subfield_code_count = _to_int(
            leader.subfield_code_count, "subfield code count (position 11)"
        )
    except (RecordLeaderInvalid, ValueError) as exc:
        return LeaderFields(error=True, error_message=str(exc))

    return LeaderFields(
        record_length=record_length,
        record_status=leader.record_status,
        type_of_record=leader.type_of_record,
        bibliographic_level=leader.bibliographic_level,
        type_of_control=leader.type_of_control,
        character_coding_scheme=leader.coding_scheme,
        indicator_count=indicator_count,
        subfield_code_count=subfield_code_count,
        base_address_of_data=base_address,
        encoding_level=leader.encoding_level,
        descriptive_cataloging_form=leader.cataloging_form,
        multipart_resource_record_level=leader.multipart_ressource,
    )
