import pymarc
from gen.axiom_context import AxiomContext
from gen.messages_pb2 import ConvertMarc8Input, ConvertMarc8Output


def convert_marc8_to_unicode(ax: AxiomContext, input: ConvertMarc8Input) -> ConvertMarc8Output:
    """Convert raw MARC-8 (ANSI/NISO Z39.47) encoded bytes -- the legacy
    character encoding many older binary MARC21 records still use for
    non-Latin scripts, diacritics, and special characters -- to Unicode
    text, independent of a full record parse. Malformed multibyte
    sequences return a structured error instead of crashing.
    """
    data = input.marc8_data
    try:
        unicode_text = pymarc.marc8_to_unicode(data, hide_utf8_warnings=input.hide_warnings)
    except (UnicodeDecodeError, ValueError, IndexError, TypeError) as exc:
        return ConvertMarc8Output(error=True, error_message=f"malformed MARC-8 input: {exc}")

    return ConvertMarc8Output(unicode_text=unicode_text)
