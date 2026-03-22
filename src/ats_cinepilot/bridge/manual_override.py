from __future__ import annotations

from pathlib import Path


class AlwaysFalseOverrideSource:
    def poll_override(self) -> bool:
        return False


class FileFlagOverrideSource:
    """
    지정한 파일이 존재하면 manual override로 본다.
    로컬 codex가 실제 키 입력/휠 입력 소스로 대체하기 전까지
    가장 단순한 emergency-stop 스위치 역할을 한다.
    """

    def __init__(self, flag_path: str | Path) -> None:
        self.flag_path = Path(flag_path)

    def poll_override(self) -> bool:
        return self.flag_path.exists()
