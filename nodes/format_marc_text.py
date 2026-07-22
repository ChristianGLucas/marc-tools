from gen.axiom_context import AxiomContext
from gen.messages_pb2 import FormatMarcTextInput, FormatMarcTextOutput
from nodes.marc_common import message_to_pymarc_record


def format_marc_text(ax: AxiomContext, input: FormatMarcTextInput) -> FormatMarcTextOutput:
    """Render a MarcRecord as a human-readable "staff view" -- one line per
    field in MARCMaker-style notation (=LDR, =245  10$aTitle ...), the same
    format ILS staff interfaces commonly show catalogers. Deterministic
    field order matches the record's own field order.
    """
    record = message_to_pymarc_record(input.record)
    return FormatMarcTextOutput(text=str(record))
