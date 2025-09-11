

global _LABEL_MAP

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

class UtilsRS():

    _LABEL_MAP = {
        "last name": "lastName",
        "first name": "firstName",
        "student id": "studentId",
        "email": "email",
        "status": "status",
        "date invited": "dateInvited",
        "last login": "lastLoginDate",
        "last registered": "lastUserRegistration.registrationDate",
        "time multiplier": "assessmentTimeMultiplier",
        "lab user": "isLabUser",
        "non-secure": "isNonSecure",
        "non-secure user": "isNonSecure",
        "action": "actions",
    }

    def normalize_label(self, label: str) -> str:
        l = label.strip().lower()
        return _LABEL_MAP.get(l, l.replace(" ", "_"))