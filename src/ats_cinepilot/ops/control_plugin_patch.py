from __future__ import annotations

from pathlib import Path
import re


GLOBAL_CONTEXT_DECL = "static input_context_t g_input_context;"
LOCAL_CONTEXT_DECL = "    input_context_t input_context;\n"
CALLBACK_CONTEXT_REF = "    device_info.callback_context = &input_context;\n"
PATCHED_CONTEXT_REF = "    device_info.callback_context = &g_input_context;\n"


def patch_scs_sdk_controller_source(source: str) -> str:
    if GLOBAL_CONTEXT_DECL in source and PATCHED_CONTEXT_REF in source:
        return source

    struct_pattern = re.compile(
        r"(struct input_context_t\s*\{\s*unsigned int input_idx = 0;\s*unsigned int shm_offset = 0;\s*\};\s*)",
        re.MULTILINE,
    )
    if not struct_pattern.search(source):
        raise ValueError("failed to locate input_context_t declaration marker")
    if LOCAL_CONTEXT_DECL not in source:
        raise ValueError("failed to locate local input_context declaration")
    if CALLBACK_CONTEXT_REF not in source:
        raise ValueError("failed to locate callback_context assignment")

    patched = struct_pattern.sub(rf"\1{GLOBAL_CONTEXT_DECL}\n\n", source, count=1)
    patched = patched.replace(LOCAL_CONTEXT_DECL, "", 1)
    patched = patched.replace(CALLBACK_CONTEXT_REF, PATCHED_CONTEXT_REF, 1)
    return patched


def patch_scs_sdk_controller_file(path: str | Path) -> bool:
    file_path = Path(path)
    original = file_path.read_text(encoding="utf-8")
    patched = patch_scs_sdk_controller_source(original)
    if patched == original:
        return False
    file_path.write_text(patched, encoding="utf-8")
    return True
