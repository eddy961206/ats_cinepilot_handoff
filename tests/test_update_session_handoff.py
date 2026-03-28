from pathlib import Path
import sys


sys.path.append(str(Path("scripts").resolve()))

from update_session_handoff import AUTO_BEGIN, AUTO_END, merge_auto_generated_section


def test_merge_auto_generated_section_replaces_managed_block_only():
    existing = "\n".join(
        [
            "# Next Agent Brief",
            "",
            "- manual note stays",
            AUTO_BEGIN,
            "- old generated facts",
            AUTO_END,
            "- trailing manual note stays too",
            "",
        ]
    )
    generated = "\n".join([AUTO_BEGIN, "- new generated facts", AUTO_END])

    merged = merge_auto_generated_section(existing, generated)

    assert "- manual note stays" in merged
    assert "- trailing manual note stays too" in merged
    assert "- old generated facts" not in merged
    assert "- new generated facts" in merged
