import secrets
from utils.db import is_id_taken

POSITION_MAP = {
    "DOCTOR": "DOC",
    "NURSE": "NUR",
    "CORPER-DOC": "CRD",
    "CORPER-NURSE": "CRN",
    "INTERN": "INT"
}

def generate_staff_id(surname: str, other_names: str, position: str) -> str:
    """
    Generates a staff ID based on name rules, position mapping, and 4 random digits.
    Returns format: XXX-XXX-XXXX
    """
    surname = surname.strip().upper()
    other_names = other_names.strip().upper()
    
    other_name_parts = other_names.split()
    
    # Rule 1: 3+ names total (Surname + 2 Other Names)
    if len(other_name_parts) >= 2:
        initials = f"{surname[0]}{other_name_parts[0][0]}{other_name_parts[1][0]}"
    # Rule 2: Exactly 2 names total (Surname + 1 Other Name)
    elif len(other_name_parts) == 1:
        if len(other_name_parts[0]) < 2:
            raise ValueError("Other name must be at least 2 characters long for ID generation.")
        initials = f"{surname[0]}{other_name_parts[0][0:2]}"
    else:
        raise ValueError("Must provide at least one other name.")
        
    pos_code = POSITION_MAP.get(position, "UNK")
    random_suffix = f"{secrets.randbelow(10000):04d}"
    
    return f"{initials}-{pos_code}-{random_suffix}"

def generate_unique_staff_id(surname: str, other_names: str, position: str) -> str:
    """Wraps generation in a loop to ensure DB uniqueness."""
    while True:
        candidate_id = generate_staff_id(surname, other_names, position)
        if not is_id_taken(candidate_id):
            return candidate_id