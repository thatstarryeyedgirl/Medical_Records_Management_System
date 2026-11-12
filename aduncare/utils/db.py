import sqlite3
import os


# ============================================================
# DATABASE PATH
# ============================================================

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "aduncare.db"
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection() -> sqlite3.Connection:
    """
    Returns a connection to the AdunCare SQLite database.
    """

    conn = sqlite3.connect(DB_PATH)

    # Enable foreign-key constraints.
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn


# ============================================================
# GENERIC COLUMN HELPER
# ============================================================

def column_exists(cursor, table_name, column_name):
    """
    Checks whether a column already exists in a table.
    """

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    return column_name in columns


def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_definition
):
    """
    Adds a column only if it does not already exist.

    This allows an existing database to be upgraded
    without deleting existing data.
    """

    if not column_exists(
        cursor,
        table_name,
        column_name
    ):
        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


# ============================================================
# DATABASE INITIALISATION
# ============================================================

def init_db():
    """
    Creates the complete AdunCare database structure.

    Existing databases are upgraded safely.
    Existing data is not deleted.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # STAFF
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            surname TEXT NOT NULL,
            other_names TEXT NOT NULL,
            position TEXT NOT NULL,
            staff_id TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            locked_until REAL DEFAULT 0
        )
    """)

    # Existing installations may not have locked_until.
    add_column_if_missing(
        cursor,
        "staff",
        "locked_until",
        "REAL DEFAULT 0"
    )

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matric_no TEXT NOT NULL UNIQUE,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            level TEXT NOT NULL,
            department TEXT,
            blood_group TEXT,
            genotype TEXT,
            rhesus_factor TEXT,
            vaccines_up_to_date TEXT DEFAULT 'NO',
            added_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add new medical fields to old databases.
    add_column_if_missing(
        cursor,
        "students",
        "blood_group",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "students",
        "genotype",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "students",
        "rhesus_factor",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "students",
        "added_by",
        "TEXT"
    )

    # --------------------------------------------------------
    # HEALTH CONDITIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id)
                ON DELETE CASCADE,
            condition TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # EMERGENCY CONTACTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id)
                ON DELETE CASCADE,
            contact_name TEXT NOT NULL,
            relationship TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # VISIT LOGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id)
                ON DELETE CASCADE,
            visit_time TEXT NOT NULL,
            reason TEXT NOT NULL,
            treatment TEXT NOT NULL,
            drug_administered TEXT,
            drug_status TEXT,
            disposition TEXT NOT NULL
        )
    """)

    # Add new drug fields to existing databases.
    add_column_if_missing(
        cursor,
        "visit_logs",
        "drug_administered",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "visit_logs",
        "drug_status",
        "TEXT"
    )

    # --------------------------------------------------------
    # COMPLIANCE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id)
                ON DELETE CASCADE,
            missing_item TEXT NOT NULL,
            deadline TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # NURSE SETTINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nurse_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# STAFF DATABASE HELPERS
# ============================================================

def add_locked_until_column():
    """
    Adds locked_until to older staff tables if required.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        add_column_if_missing(
            cursor,
            "staff",
            "locked_until",
            "REAL DEFAULT 0"
        )

        conn.commit()

        print("Database update completed successfully.")

    except sqlite3.OperationalError as e:
        print("Database update:", e)

    finally:
        conn.close()


def is_id_taken(staff_id: str) -> bool:
    """
    Checks whether a staff ID already exists.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM staff WHERE staff_id = ?",
        (staff_id,)
    )

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


def is_phone_taken(phone: str) -> bool:
    """
    Checks whether a phone number already exists.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM staff WHERE phone = ?",
        (phone,)
    )

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


def is_email_taken(email: str) -> bool:
    """
    Checks whether an email already exists.
    """

    if not email:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM staff WHERE email = ?",
        (email,)
    )

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


def insert_staff(
    surname: str,
    other_names: str,
    position: str,
    staff_id: str,
    phone: str,
    email: str,
    password_hash: str
):
    """
    Inserts a new staff member.
    """

    conn = get_connection()
    cursor = conn.cursor()

    email_val = email if email else None

    cursor.execute("""
        INSERT INTO staff (
            surname,
            other_names,
            position,
            staff_id,
            phone,
            email,
            password_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        surname,
        other_names,
        position,
        staff_id,
        phone,
        email_val,
        password_hash
    ))

    conn.commit()
    conn.close()


# ============================================================
# START DATABASE WHEN FILE IS RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("AdunCare database initialised.")
    print(f"Database location: {os.path.abspath(DB_PATH)}")
    print("=" * 60)
    
    