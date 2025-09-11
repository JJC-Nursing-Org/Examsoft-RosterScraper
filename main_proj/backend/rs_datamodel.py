
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Sequence

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class StudentRow:
    last_name: str = ""
    first_name: str = ""
    student_id: str = ""
    status: str = ""
    email: str = ""
    date_invited: str = ""
    last_login: str = ""
    last_registered: str = ""
    is_lab_user: str = ""
    is_non_secure: str = ""
    time_multiplier: str = ""
    action: str = ""

    @classmethod
    def from_cellmap(cls, cellmap: Dict[str, str]) -> "StudentRow":
        def yesno(text: Optional[str]) -> str:
            t = (text or "").strip()
            return "Yes" if t else "No"
        s = cellmap.get("status", "").strip()
        return cls(
            last_name=cellmap.get("lastName", "").strip(),
            first_name=cellmap.get("firstName", "").strip(),
            student_id=cellmap.get("studentId", "").strip().zfill(7),
            status=s,
            email=cellmap.get("email", "").strip(),
            date_invited=cellmap.get("dateInvited", "").strip(),
            last_login=cellmap.get("lastLoginDate", "").strip(),
            last_registered=cellmap.get("lastUserRegistration.registrationDate", "").strip(),
            is_lab_user=yesno(cellmap.get("isLabUser")),
            is_non_secure=yesno(cellmap.get("isNonSecure")),
            time_multiplier=cellmap.get("assessmentTimeMultiplier", "").strip(),
            action=s,
        )