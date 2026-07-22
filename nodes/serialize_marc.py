from gen.axiom_context import AxiomContext
from gen.messages_pb2 import SerializeMarcInput, SerializeMarcOutput
from nodes.marc_common import (
    MarcToolsError,
    message_to_pymarc_record,
    serialize_records,
)


def serialize_marc(ax: AxiomContext, input: SerializeMarcInput) -> SerializeMarcOutput:
    """Render one or more canonical MarcRecord envelopes back into binary
    MARC21 (ISO 2709), MARCXML, or MARC-in-JSON bytes. An empty records list
    or an unrecognized format returns a structured error instead of raising.
    """
    try:
        records = [message_to_pymarc_record(record) for record in input.records]
        data = serialize_records(records, input.format)
    except MarcToolsError as exc:
        return SerializeMarcOutput(error=True, error_message=str(exc))

    return SerializeMarcOutput(data=data)
