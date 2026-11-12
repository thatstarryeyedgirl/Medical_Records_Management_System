import re


# ============================================================
# DEPARTMENT CODES
# ============================================================

DEPARTMENT_CODES = {
    "CYB": "Cyber Security",
    "SEN": "Software Engineering",
    "FRS": "Forensic Science",
    "COM": "Computer Science",
    "BIO": "Biology",
    "LAW": "Law",
}


# ============================================================
# NAME VALIDATION
# ============================================================

def validate_name(name: str) -> bool:
    """Validates a person's name."""
    if not name or not name.strip():
        return False

    return bool(
        re.fullmatch(
            r"[A-Za-z\s'\-]+",
            name.strip()
        )
    )


# ============================================================
# PHONE VALIDATION
# ============================================================

def validate_phone(phone: str) -> bool:
    """Validates accepted Nigerian phone number formats."""
    if not phone or not phone.strip():
        return False

    phone = phone.strip()

    local_pattern = r"^(070|080|081|090)\d{8}$"
    international_pattern = r"^\+234\s?(70|80|81|90)\d{8}$"

    return bool(
        re.fullmatch(local_pattern, phone)
        or re.fullmatch(international_pattern, phone)
    )


# ============================================================
# EMAIL VALIDATION
# ============================================================

def validate_email(email: str) -> bool:
    """Validates a standard email address. Empty is allowed."""
    if not email or not email.strip():
        return True

    pattern = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"

    return bool(
        re.fullmatch(
            pattern,
            email.strip()
        )
    )


# ============================================================
# PASSWORD STRENGTH
# ============================================================

def evaluate_password_strength(password: str) -> str:
    """Evaluates password strength."""
    if len(password) < 8:
        return "Invalid"

    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"[0-9]", password))
    has_special = bool(
        re.search(
            r"[!@#$%^&*()_+\-=\?</>\.]",
            password
        )
    )

    score = sum([
        has_upper,
        has_lower,
        has_digit,
        has_special
    ])

    if score == 4:
        return "Strong"
    if score == 3:
        return "Medium"
    if score >= 1:
        return "Weak"
    return "Invalid"


# ============================================================
# MATRIC NUMBER VALIDATION
# ============================================================

def validate_matric_number(matric_number: str) -> bool:
    """Validates an ADUN matriculation number."""
    if not matric_number:
        return False

    matric_number = matric_number.strip().upper()

    pattern = (
        r"^ADUN/FS/"
        r"(CYB|SEN|FRS|COM|BIO|LAW)"
        r"/\d{2}"
        r"/\d{3,}$"
    )

    return bool(
        re.fullmatch(
            pattern,
            matric_number
        )
    )


# ============================================================
# DEPARTMENT FROM MATRIC NUMBER
# ============================================================

def get_department_from_matric(matric_number: str):
    """Extracts the department from a valid matric number."""
    if not matric_number:
        return None

    matric_number = matric_number.strip().upper()

    if not validate_matric_number(matric_number):
        return None

    parts = matric_number.split("/")
    department_code = parts[2]

    return DEPARTMENT_CODES.get(department_code)
