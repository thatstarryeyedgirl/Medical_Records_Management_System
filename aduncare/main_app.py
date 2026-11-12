import re
import os
import sqlite3
import csv
import hashlib
import time
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import bcrypt
from PIL import Image

from utils.db import DB_PATH, init_db
from utils.validation import (
    validate_matric_number,
    get_department_from_matric,
    validate_name,
    validate_phone,
    validate_email,
)


# ============================================================
# COLOURS
# ============================================================

PRIMARY       = "#0ea5e9"
PRIMARY_HOVER = "#0284c7"
DANGER        = "#ef4444"
WARNING       = "#f59e0b"
SUCCESS       = "#10b981"

TEXT_MAIN     = "#1e293b"
TEXT_LIGHT    = "#64748b"

CARD_BG       = "#f0f9ff"
SIDEBAR_BG    = "#e0f2fe"
APP_BG        = "#bae6fd"

ALERT_PILL_BG = "#fee2e2"
ALERT_PILL_FG = "#991b1b"


# ============================================================
# DATABASE
# ============================================================

DB_NAME = DB_PATH

print("=" * 60)
print("DATABASE USED BY MAIN_APP:")
print(os.path.abspath(DB_NAME))
print("=" * 60)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "LOGO ADUNCARE.png"
)


# ============================================================
# OPTIONS
# ============================================================

LEVEL_OPTIONS = [
    "100 LEVEL",
    "200 LEVEL",
    "300 LEVEL",
    "400 LEVEL",
    "500 LEVEL"
]

VACCINE_OPTIONS = [
    "YES",
    "NO"
]

BLOOD_GROUP_OPTIONS = [
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-"
]

GENOTYPE_OPTIONS = [
    "AA",
    "AS",
    "AC",
    "SS",
    "SC"
]

RHESUS_OPTIONS = [
    "Positive (+)",
    "Negative (-)"
]

RELATIONSHIP_OPTIONS = [
    "Mother",
    "Father",
    "Sister",
    "Brother",
    "Aunt",
    "Uncle",
    "Grandmother",
    "Grandfather",
    "Guardian",
    "Parent",
    "Lecturer",
    "Friend",
    "Boyfriend",
    "Girlfriend",
    "Spouse",
    "Roommate",
    "Best Friend",
    "Other"
]

DRUG_STATUS_OPTIONS = [
    "Administered at Clinic",
    "Prescribed",
    "Advised to Buy Elsewhere",
    "No Drug Required"
]

DISPOSITION_OPTIONS = [
    "Returned to Class",
    "Sent Home",
    "911 / Emergency"
]


FERPA_LOCK_SECONDS = 180


# ============================================================
# DATABASE INITIALISATION
# ============================================================

def ensure_database():
    """
    Creates/updates the database without deleting existing data.
    """

    init_db()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Safety check for older versions of the database.
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(staff)")
    staff_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "locked_until" not in staff_columns:
        cursor.execute(
            "ALTER TABLE staff ADD COLUMN locked_until REAL DEFAULT 0"
        )

    # --------------------------------------------------------
    # STUDENT COLUMNS
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(students)")
    student_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "blood_group" not in student_columns:
        cursor.execute(
            "ALTER TABLE students ADD COLUMN blood_group TEXT"
        )

    if "genotype" not in student_columns:
        cursor.execute(
            "ALTER TABLE students ADD COLUMN genotype TEXT"
        )

    if "rhesus_factor" not in student_columns:
        cursor.execute(
            "ALTER TABLE students ADD COLUMN rhesus_factor TEXT"
        )

    if "added_by" not in student_columns:
        cursor.execute(
            "ALTER TABLE students ADD COLUMN added_by TEXT"
        )

    # --------------------------------------------------------
    # VISIT LOG COLUMNS
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(visit_logs)")
    visit_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "drug_administered" not in visit_columns:
        cursor.execute(
            "ALTER TABLE visit_logs ADD COLUMN drug_administered TEXT"
        )

    if "drug_status" not in visit_columns:
        cursor.execute(
            "ALTER TABLE visit_logs ADD COLUMN drug_status TEXT"
        )

    conn.commit()
    conn.close()


# ============================================================
# INITIALISE DATABASE
# ============================================================

ensure_database()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_staff_display_name(staff):
    """
    Creates the staff member's display name from the database's
    surname + other_names structure.

    Example:

        surname = Jones
        other_names = Sarah

    returns:

        Sarah Jones
    """

    if not staff:
        return ""

    surname = str(
        staff.get("surname", "")
    ).strip()

    other_names = str(
        staff.get("other_names", "")
    ).strip()

    if other_names and surname:
        return f"{other_names} {surname}"

    return other_names or surname


def get_staff_position(staff):
    """
    Returns the staff position safely.
    """

    if not staff:
        return ""

    return str(
        staff.get("position", "")
    ).strip().lower()


# ============================================================
# LOGIN WINDOW
# ============================================================

class LoginWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("AdunCare - Staff Login")
        self.geometry("480x620")
        self.resizable(False, False)

        self.configure(
            fg_color="#53c4c8"
        )

        self.failed_attempts = {}

        # ----------------------------------------------------
        # LOGIN CARD
        # ----------------------------------------------------

        self.card = ctk.CTkFrame(
            self,
            fg_color="#8cdadb",
            corner_radius=20,
            width=400,
            height=520
        )

        self.card.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.card.pack_propagate(False)

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        try:
            self.login_logo_image = ctk.CTkImage(
                Image.open(LOGO_PATH),
                size=(204, 80)
            )

            ctk.CTkLabel(
                self.card,
                text="",
                image=self.login_logo_image
            ).pack(
                pady=(35, 5)
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # STAFF ID
        # ----------------------------------------------------

        self.lbl_id = ctk.CTkLabel(
            self.card,
            text="ID NUMBER",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color="#1e1e1e"
        )

        self.lbl_id.pack(
            anchor="w",
            padx=40,
            pady=(10, 0)
        )

        self.id_entry = ctk.CTkEntry(
            self.card,
            height=45,
            fg_color="#e9f8f8",
            border_color="#000000",
            border_width=2,
            corner_radius=8,
            text_color="black"
        )

        self.id_entry.pack(
            fill="x",
            padx=40,
            pady=(5, 15)
        )

        self.id_entry.bind(
            "<KeyRelease>",
            self._format_id_input
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        self.lbl_pass = ctk.CTkLabel(
            self.card,
            text="PASSWORD",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color="#1e1e1e"
        )

        self.lbl_pass.pack(
            anchor="w",
            padx=40
        )

        self.pass_entry = ctk.CTkEntry(
            self.card,
            height=45,
            fg_color="#e9f8f8",
            border_color="#000000",
            border_width=2,
            corner_radius=8,
            show="*",
            text_color="black"
        )

        self.pass_entry.pack(
            fill="x",
            padx=40,
            pady=(5, 5)
        )

        # ----------------------------------------------------
        # ERROR LABEL
        # ----------------------------------------------------

        self.lbl_error = ctk.CTkLabel(
            self.card,
            text="",
            text_color="#d93025",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        )

        self.lbl_error.pack(
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # LOGIN BUTTON
        # ----------------------------------------------------

        self.btn_login = ctk.CTkButton(
            self.card,
            text="LOGIN",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            fg_color="#3a5a78",
            hover_color="#2c455c",
            text_color="white",
            corner_radius=8,
            height=50,
            command=self._attempt_login
        )

        self.btn_login.pack(
            fill="x",
            padx=40,
            pady=(10, 20)
        )

        self.bind(
            "<Return>",
            lambda event: self._attempt_login()
        )

    # ========================================================
    # STAFF ID FORMATTING
    # ========================================================

    def _format_id_input(self, event):

        if event.keysym in (
            "BackSpace",
            "Delete",
            "Left",
            "Right"
        ):
            return

        raw_text = (
            self.id_entry
            .get()
            .replace("-", "")
            .upper()
        )

        formatted = ""

        for i, char in enumerate(raw_text):
            if i == 3 or i == 6:
                formatted += "-"

            formatted += char

        formatted = formatted[:12]

        self.id_entry.delete(
            0,
            "end"
        )

        self.id_entry.insert(
            0,
            formatted
        )

    # ========================================================
    # LOGIN
    # ========================================================

    def _attempt_login(self):

        id_val = (
            self.id_entry
            .get()
            .strip()
            .upper()
        )

        pass_val = self.pass_entry.get()

        if not id_val or not pass_val:
            self.lbl_error.configure(
                text="Please enter ID and password."
            )
            return

        if not re.fullmatch(
            r"^[A-Z]{3}-[A-Z]{3}-\d{4}$",
            id_val
        ):
            self.lbl_error.configure(
                text="Please enter a valid ID and password."
            )
            return

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM staff WHERE staff_id=?",
            (id_val,)
        )

        user = cursor.fetchone()

        if user:

            locked_until = (
                user["locked_until"]
                if "locked_until" in user.keys()
                and user["locked_until"] is not None
                else 0
            )

            if locked_until > time.time():

                self._start_lockout_ui(
                    locked_until,
                    id_val
                )

                conn.close()
                return

            try:

                is_valid = bcrypt.checkpw(
                    pass_val.encode("utf-8"),
                    user["password_hash"].encode("utf-8")
                )

            except (ValueError, AttributeError):

                is_valid = (
                    hashlib.sha256(
                        pass_val.encode()
                    ).hexdigest()
                    == user["password_hash"]
                )

            if is_valid:

                cursor.execute(
                    """
                    UPDATE staff
                    SET locked_until=0
                    WHERE staff_id=?
                    """,
                    (id_val,)
                )

                conn.commit()

                logged_user = dict(user)

                conn.close()

                self.destroy()

                app = ClinicPortalApp(
                    logged_in_user=logged_user
                )

                app.mainloop()

                return

            else:

                self.failed_attempts[id_val] = (
                    self.failed_attempts.get(
                        id_val,
                        0
                    ) + 1
                )

                if self.failed_attempts[id_val] >= 4:

                    lock_time = (
                        time.time() + 60
                    )

                    cursor.execute(
                        """
                        UPDATE staff
                        SET locked_until=?
                        WHERE staff_id=?
                        """,
                        (
                            lock_time,
                            id_val
                        )
                    )

                    conn.commit()

                    self._start_lockout_ui(
                        lock_time,
                        id_val
                    )

                    conn.close()
                    return

        self.lbl_error.configure(
            text="Invalid ID number or password."
        )

        self.pass_entry.delete(
            0,
            "end"
        )

        conn.close()

    # ========================================================
    # LOCKOUT UI
    # ========================================================

    def _start_lockout_ui(
        self,
        unlock_time,
        id_val
    ):

        self.id_entry.configure(
            state="disabled"
        )

        self.pass_entry.configure(
            state="disabled"
        )

        self.btn_login.configure(
            state="disabled"
        )

        self._update_countdown(
            unlock_time,
            id_val
        )

    def _update_countdown(
        self,
        unlock_time,
        id_val
    ):

        remaining = int(
            unlock_time - time.time()
        )

        if remaining > 0:

            self.lbl_error.configure(
                text=f"Locked out. Try again in {remaining}s"
            )

            self.after(
                1000,
                lambda: self._update_countdown(
                    unlock_time,
                    id_val
                )
            )

        else:

            self.id_entry.configure(
                state="normal"
            )

            self.pass_entry.configure(
                state="normal"
            )

            self.btn_login.configure(
                state="normal"
            )

            self.pass_entry.delete(
                0,
                "end"
            )

            self.lbl_error.configure(
                text=""
            )

            self.failed_attempts[id_val] = 0

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE staff
                SET locked_until=0
                WHERE staff_id=?
                """,
                (id_val,)
            )

            conn.commit()
            conn.close()

    # ========================================================
    # AFTER / DESTROY
    # ========================================================

    def after(
        self,
        ms,
        func=None,
        *args
    ):

        task_id = super().after(
            ms,
            func,
            *args
        )

        if not hasattr(
            self,
            "pending_tasks"
        ):
            self.pending_tasks = []

        self.pending_tasks.append(
            task_id
        )

        return task_id

    def destroy(self):

        if hasattr(
            self,
            "pending_tasks"
        ):

            for task_id in self.pending_tasks:

                try:
                    self.after_cancel(
                        task_id
                    )

                except Exception:
                    pass

        super().destroy()


# ============================================================
# MAIN CLINIC APPLICATION
# ============================================================

class ClinicPortalApp(ctk.CTk):

    def __init__(
        self,
        logged_in_user=None
    ):

        super().__init__()

        self.logged_in_user = logged_in_user

        self.title(
            "AdunCare — School Health"
        )

        self.geometry(
            "1200x750"
        )

        self.minsize(
            1200,
            750
        )

        self.configure(
            fg_color=APP_BG
        )

        ctk.set_appearance_mode(
            "light"
        )

        self.font_body = (
            "Segoe UI",
            13
        )

        self.font_heading = (
            "Segoe UI",
            18,
            "bold"
        )

        self.font_bold = (
            "Segoe UI",
            13,
            "bold"
        )

        self.conn = sqlite3.connect(
            DB_NAME
        )

        self.conn.execute(
            "PRAGMA foreign_keys = ON;"
        )

        self._init_db()

        self._build_layout()

        self._show_view(
            "directory"
        )

        # ----------------------------------------------------
        # FERPA ACTIVITY
        # ----------------------------------------------------

        self._locked = False

        # FERPA screen locking is a clinic-wide privacy policy.
        self.ferpa_enabled = True

        self.last_activity = time.time()

        self.bind_all(
            "<Motion>",
            self._reset_activity
        )

        self.bind_all(
            "<KeyPress>",
            self._reset_activity
        )

        self.bind_all(
            "<Button>",
            self._reset_activity
        )

        self.after(
            5000,
            self._check_idle
        )

    # ========================================================
    # DATABASE
    # ========================================================

    def _init_db(self):
        ensure_database()

    # ========================================================
    # LAYOUT
    # ========================================================

    def _build_layout(self):

        self.grid_columnconfigure(
            1,
            weight=1
        )

        self.grid_rowconfigure(
            0,
            weight=1
        )

        # ----------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------

        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=220,
            fg_color=SIDEBAR_BG,
            corner_radius=16
        )

        self.sidebar_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )

        self.sidebar_frame.grid_propagate(
            False
        )

        try:

            self.sidebar_logo_image = ctk.CTkImage(
                Image.open(LOGO_PATH),
                size=(180, 60)
            )

            ctk.CTkLabel(
                self.sidebar_frame,
                text="",
                image=self.sidebar_logo_image
            ).pack(
                pady=(20, 30)
            )

        except Exception:

            logo_label = ctk.CTkLabel(
                self.sidebar_frame,
                text="AdunCare",
                font=(
                    "Segoe UI",
                    20,
                    "bold"
                ),
                text_color=PRIMARY
            )

            logo_label.pack(
                pady=(20, 30)
            )

        # ----------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------

        self.nav_buttons = {}

        nav_items = [
            (
                "directory",
                "Student Directory"
            ),
            (
                "visits",
                "Visit Logs"
            ),
            (
                "compliance",
                "Compliance"
            ),
            (
                "settings",
                "Settings"
            )
        ]

        for view_id, text in nav_items:

            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                font=self.font_bold,
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_LIGHT,
                hover_color="#dbeafe",
                command=lambda vid=view_id:
                    self._show_view(vid)
            )

            btn.pack(
                fill="x",
                padx=15,
                pady=5
            )

            self.nav_buttons[
                view_id
            ] = btn

        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        self.content_container = ctk.CTkFrame(
            self,
            fg_color=APP_BG
        )

        self.content_container.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )

        self.content_container.grid_columnconfigure(
            0,
            weight=1
        )

        self.content_container.grid_rowconfigure(
            0,
            weight=1
        )

        self.views = {}

        self.views[
            "directory"
        ] = self._build_directory_view()

        self.views[
            "visits"
        ] = self._build_visits_view()

        self.views[
            "compliance"
        ] = self._build_compliance_view()

        self.views[
            "settings"
        ] = self._build_settings_view()

    # ========================================================
    # SHOW VIEW
    # ========================================================

    def _show_view(
        self,
        view_id
    ):

        for frame in self.views.values():

            frame.grid_forget()

        for vid, btn in self.nav_buttons.items():

            btn.configure(
                fg_color="transparent",
                text_color=TEXT_LIGHT
            )

        self.views[
            view_id
        ].grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.nav_buttons[
            view_id
        ].configure(
            fg_color=PRIMARY,
            text_color="white"
        )

        if view_id == "directory":

            self._refresh_directory()

        elif view_id == "visits":

            self._refresh_visits()

        elif view_id == "compliance":

            self._refresh_compliance()

    # ========================================================
    # DIRECTORY VIEW
    # ========================================================

    def _build_directory_view(self):

        frame = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )

        header_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        header_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            header_frame,
            text="Student Directory",
            font=self.font_heading,
            text_color=TEXT_MAIN
        ).pack(
            side="left"
        )

        ctk.CTkButton(
            header_frame,
            text="＋ Add New Student",
            font=self.font_bold,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            corner_radius=20,
            command=self._add_student_dialog
        ).pack(
            side="right"
        )

        # ----------------------------------------------------
        # TOOLBAR
        # ----------------------------------------------------

        toolbar = ctk.CTkFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12
        )

        toolbar.pack(
            fill="x",
            pady=(0, 15),
            ipady=5
        )

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search name or matric no...",
            width=250,
            corner_radius=20
        )

        self.search_entry.pack(
            side="left",
            padx=10,
            pady=10
        )

        self.search_entry.bind(
            "<KeyRelease>",
            lambda e:
                self._refresh_directory()
        )

        self.level_filter = ctk.CTkComboBox(
            toolbar,
            values=[
                "All Levels"
            ] + LEVEL_OPTIONS,
            command=lambda e:
                self._refresh_directory(),
            corner_radius=20
        )

        self.level_filter.set(
            "All Levels"
        )

        self.level_filter.pack(
            side="left",
            padx=10
        )

        # ----------------------------------------------------
        # DYNAMIC CONDITION FILTER
        # ----------------------------------------------------

        self.condition_filter = ctk.CTkComboBox(
            toolbar,
            values=[
                "All Conditions"
            ],
            command=lambda e:
                self._refresh_directory(),
            corner_radius=20
        )

        self.condition_filter.set(
            "All Conditions"
        )

        self.condition_filter.pack(
            side="left",
            padx=10
        )

        self._refresh_condition_filter_options()

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        self.dir_table = ctk.CTkScrollableFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12
        )

        self.dir_table.pack(
            fill="both",
            expand=True
        )

        self.dir_table.grid_columnconfigure(
            (0, 1, 2, 3, 4),
            weight=1
        )

        return frame

    # ========================================================
    # CONDITION FILTER OPTIONS
    # ========================================================

    def _refresh_condition_filter_options(self):

        try:

            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT condition
                FROM health_conditions
                WHERE TRIM(condition) != ''
                ORDER BY condition COLLATE NOCASE
                """
            )

            conditions = [
                row[0]
                for row in cursor.fetchall()
            ]

            values = [
                "All Conditions"
            ] + conditions

            current = (
                self.condition_filter.get()
                if hasattr(
                    self,
                    "condition_filter"
                )
                else "All Conditions"
            )

            self.condition_filter.configure(
                values=values
            )

            if current in values:
                self.condition_filter.set(
                    current
                )
            else:
                self.condition_filter.set(
                    "All Conditions"
                )

        except Exception:
            pass

    # ========================================================
    # REFRESH DIRECTORY
    # ========================================================

    def _refresh_directory(self):

        if not hasattr(
            self,
            "dir_table"
        ):
            return

        self._refresh_condition_filter_options()

        for widget in self.dir_table.winfo_children():
            widget.destroy()

        headers = [
            "STUDENT",
            "MATRIC NO. • LEVEL",
            "EMERGENCY CONTACT",
            "HEALTH CONDITIONS",
            "ACTIONS"
        ]

        for col, text in enumerate(headers):

            ctk.CTkLabel(
                self.dir_table,
                text=text,
                font=(
                    "Segoe UI",
                    11,
                    "bold"
                ),
                text_color=TEXT_LIGHT
            ).grid(
                row=0,
                column=col,
                sticky="w",
                padx=10,
                pady=(10, 5)
            )

        search_term = (
            f"%{self.search_entry.get()}%"
        )

        level_val = (
            self.level_filter.get()
        )

        cond_val = (
            self.condition_filter.get()
        )

        query = """
            SELECT
                id,
                matric_no,
                last_name,
                first_name,
                level
            FROM students
            WHERE (
                last_name LIKE ?
                OR first_name LIKE ?
                OR matric_no LIKE ?
            )
        """

        params = [
            search_term,
            search_term,
            search_term
        ]

        if level_val != "All Levels":

            query += """
                AND level = ?
            """

            params.append(
                level_val
            )

        if cond_val != "All Conditions":

            query += """
                AND id IN (
                    SELECT student_id
                    FROM health_conditions
                    WHERE condition = ?
                )
            """

            params.append(
                cond_val
            )

        query += """
            ORDER BY last_name COLLATE NOCASE
        """

        cursor = self.conn.cursor()

        cursor.execute(
            query,
            params
        )

        students = cursor.fetchall()

        for row_idx, row in enumerate(
            students,
            start=1
        ):

            (
                db_id,
                matric_no,
                lname,
                fname,
                level
            ) = row

            ctk.CTkLabel(
                self.dir_table,
                text=f"{lname}, {fname}",
                font=self.font_bold,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=0,
                sticky="w",
                padx=10,
                pady=10
            )

            ctk.CTkLabel(
                self.dir_table,
                text=f"{matric_no} • {level}",
                font=self.font_body,
                text_color=TEXT_LIGHT
            ).grid(
                row=row_idx,
                column=1,
                sticky="w",
                padx=10,
                pady=10
            )

            cursor.execute(
                """
                SELECT contact_name, phone
                FROM emergency_contacts
                WHERE student_id = ?
                LIMIT 1
                """,
                (db_id,)
            )

            contact = cursor.fetchone()

            if contact:

                contact_text = (
                    f"{contact[0]} ({contact[1]})"
                )

            else:

                contact_text = "No contact"

            ctk.CTkLabel(
                self.dir_table,
                text=contact_text,
                font=self.font_body,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=2,
                sticky="w",
                padx=10,
                pady=10
            )

            cursor.execute(
                """
                SELECT condition
                FROM health_conditions
                WHERE student_id = ?
                ORDER BY condition COLLATE NOCASE
                """,
                (db_id,)
            )

            conditions = [
                r[0]
                for r in cursor.fetchall()
            ]

            cond_frame = ctk.CTkFrame(
                self.dir_table,
                fg_color="transparent"
            )

            cond_frame.grid(
                row=row_idx,
                column=3,
                sticky="w",
                padx=10,
                pady=10
            )

            if conditions:

                for cond in conditions:

                    ctk.CTkLabel(
                        cond_frame,
                        text=f" {cond} ",
                        fg_color=ALERT_PILL_BG,
                        text_color=ALERT_PILL_FG,
                        corner_radius=12,
                        font=(
                            "Segoe UI",
                            11
                        )
                    ).pack(
                        side="left",
                        padx=2
                    )

            else:

                ctk.CTkLabel(
                    cond_frame,
                    text="None",
                    text_color=TEXT_LIGHT
                ).pack()

            ctk.CTkButton(
                self.dir_table,
                text="View Profile",
                width=80,
                fg_color="transparent",
                border_width=1,
                text_color=PRIMARY,
                border_color=PRIMARY,
                command=lambda sid=db_id:
                    self._view_student_profile(sid)
            ).grid(
                row=row_idx,
                column=4,
                sticky="w",
                padx=10,
                pady=10
            )

    # ========================================================
    # VISIT VIEW
    # ========================================================

    def _build_visits_view(self):

        frame = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )

        header_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        header_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            header_frame,
            text="Clinic Visit Logs",
            font=self.font_heading,
            text_color=TEXT_MAIN
        ).pack(
            side="left"
        )

        btn_frame = ctk.CTkFrame(
            header_frame,
            fg_color="transparent"
        )

        btn_frame.pack(
            side="right"
        )

        ctk.CTkButton(
            btn_frame,
            text="Export CSV",
            fg_color="transparent",
            border_width=1,
            border_color=TEXT_LIGHT,
            text_color=TEXT_MAIN,
            corner_radius=20,
            command=self._export_csv
        ).pack(
            side="left",
            padx=10
        )

        ctk.CTkButton(
            btn_frame,
            text="＋ Log New Visit",
            font=self.font_bold,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            corner_radius=20,
            command=self._log_visit_dialog
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # TOOLBAR
        # ----------------------------------------------------

        toolbar = ctk.CTkFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12
        )

        toolbar.pack(
            fill="x",
            pady=(0, 15),
            ipady=5
        )

        today_str = datetime.now().strftime(
            "%Y-%m-%d"
        )

        ctk.CTkLabel(
            toolbar,
            text="From:",
            text_color=TEXT_MAIN
        ).pack(
            side="left",
            padx=(15, 5)
        )

        self.date_start = ctk.CTkEntry(
            toolbar,
            width=120,
            corner_radius=20
        )

        self.date_start.insert(
            0,
            today_str
        )

        self.date_start.pack(
            side="left",
            padx=5,
            pady=10
        )

        ctk.CTkLabel(
            toolbar,
            text="To:",
            text_color=TEXT_MAIN
        ).pack(
            side="left",
            padx=5
        )

        self.date_end = ctk.CTkEntry(
            toolbar,
            width=120,
            corner_radius=20
        )

        self.date_end.insert(
            0,
            today_str
        )

        self.date_end.pack(
            side="left",
            padx=5
        )

        self.date_start.bind(
            "<KeyRelease>",
            lambda e:
                self._refresh_visits()
        )

        self.date_end.bind(
            "<KeyRelease>",
            lambda e:
                self._refresh_visits()
        )

        self.disp_filter = ctk.CTkComboBox(
            toolbar,
            values=[
                "All Dispositions"
            ] + DISPOSITION_OPTIONS,
            command=lambda e:
                self._refresh_visits(),
            corner_radius=20
        )

        self.disp_filter.set(
            "All Dispositions"
        )

        self.disp_filter.pack(
            side="left",
            padx=20
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        self.visit_table = ctk.CTkScrollableFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12
        )

        self.visit_table.pack(
            fill="both",
            expand=True
        )

        self.visit_table.grid_columnconfigure(
            (0, 1, 2, 3, 4, 5),
            weight=1
        )

        return frame

    # ========================================================
    # REFRESH VISITS
    # ========================================================

    def _refresh_visits(self):

        if not hasattr(
            self,
            "visit_table"
        ):
            return

        for widget in self.visit_table.winfo_children():
            widget.destroy()

        headers = [
            "TIME",
            "STUDENT",
            "REASON",
            "TREATMENT",
            "DRUG",
            "DISPOSITION"
        ]

        for col, text in enumerate(headers):

            ctk.CTkLabel(
                self.visit_table,
                text=text,
                font=(
                    "Segoe UI",
                    11,
                    "bold"
                ),
                text_color=TEXT_LIGHT
            ).grid(
                row=0,
                column=col,
                sticky="w",
                padx=10,
                pady=(10, 5)
            )

        start_date = (
            self.date_start.get().strip()
        )

        end_date = (
            self.date_end.get().strip()
        )

        disp_val = (
            self.disp_filter.get()
        )

        query = """
            SELECT
                v.visit_time,
                s.last_name,
                s.first_name,
                v.reason,
                v.treatment,
                v.drug_administered,
                v.drug_status,
                v.disposition
            FROM visit_logs v
            JOIN students s
                ON v.student_id = s.id
            WHERE v.visit_time >= ?
            AND v.visit_time <= ?
        """

        params = [
            f"{start_date} 00:00",
            f"{end_date} 23:59"
        ]

        if disp_val != "All Dispositions":

            query += """
                AND v.disposition = ?
            """

            params.append(
                disp_val
            )

        query += """
            ORDER BY v.visit_time DESC
        """

        cursor = self.conn.cursor()

        cursor.execute(
            query,
            params
        )

        visits = cursor.fetchall()

        for row_idx, row in enumerate(
            visits,
            start=1
        ):

            (
                v_time,
                lname,
                fname,
                reason,
                treatment,
                drug,
                drug_status,
                disp
            ) = row

            ctk.CTkLabel(
                self.visit_table,
                text=v_time,
                font=self.font_body,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=0,
                sticky="w",
                padx=10,
                pady=10
            )

            ctk.CTkLabel(
                self.visit_table,
                text=f"{lname}, {fname}",
                font=self.font_bold,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=1,
                sticky="w",
                padx=10,
                pady=10
            )

            ctk.CTkLabel(
                self.visit_table,
                text=reason,
                font=self.font_body,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=2,
                sticky="w",
                padx=10,
                pady=10
            )

            ctk.CTkLabel(
                self.visit_table,
                text=treatment,
                font=self.font_body,
                text_color=TEXT_MAIN,
                wraplength=160,
                justify="left"
            ).grid(
                row=row_idx,
                column=3,
                sticky="w",
                padx=10,
                pady=10
            )

            if drug:

                drug_text = drug

                if drug_status:
                    drug_text += (
                        f"\n({drug_status})"
                    )

            else:

                drug_text = (
                    drug_status
                    or "No drug recorded"
                )

            ctk.CTkLabel(
                self.visit_table,
                text=drug_text,
                font=self.font_body,
                text_color=TEXT_MAIN,
                wraplength=160,
                justify="left"
            ).grid(
                row=row_idx,
                column=4,
                sticky="w",
                padx=10,
                pady=10
            )

            color = (
                SUCCESS
                if disp == "Returned to Class"
                else (
                    DANGER
                    if disp == "911 / Emergency"
                    else WARNING
                )
            )

            ctk.CTkLabel(
                self.visit_table,
                text=disp,
                font=self.font_bold,
                text_color=color
            ).grid(
                row=row_idx,
                column=5,
                sticky="w",
                padx=10,
                pady=10
            )

    # ========================================================
    # EXPORT CSV
    # ========================================================

    def _export_csv(self):

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                (
                    "CSV files",
                    "*.csv"
                )
            ]
        )

        if not file_path:
            return

        start_date = (
            self.date_start.get()
        )

        end_date = (
            self.date_end.get()
        )

        disp_val = (
            self.disp_filter.get()
        )

        query = """
            SELECT
                v.visit_time,
                s.last_name,
                s.first_name,
                v.reason,
                v.treatment,
                v.drug_administered,
                v.drug_status,
                v.disposition
            FROM visit_logs v
            JOIN students s
                ON v.student_id = s.id
            WHERE v.visit_time >= ?
            AND v.visit_time <= ?
        """

        params = [
            f"{start_date} 00:00",
            f"{end_date} 23:59"
        ]

        if disp_val != "All Dispositions":

            query += """
                AND v.disposition = ?
            """

            params.append(
                disp_val
            )

        query += """
            ORDER BY v.visit_time DESC
        """

        cursor = self.conn.cursor()

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

        try:

            with open(
                file_path,
                mode="w",
                newline="",
                encoding="utf-8"
            ) as f:

                writer = csv.writer(f)

                writer.writerow([
                    "Time",
                    "Student Last",
                    "Student First",
                    "Reason",
                    "Treatment",
                    "Drug Administered",
                    "Drug Status",
                    "Disposition"
                ])

                writer.writerows(rows)

            messagebox.showinfo(
                "Export Successful",
                f"Data exported to {file_path}"
            )

        except Exception as exc:

            messagebox.showerror(
                "Export Error",
                f"Could not export the file.\n\n{exc}"
            )

    # ========================================================
    # COMPLIANCE VIEW
    # ========================================================

    def _build_compliance_view(self):

        frame = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )

        header_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        header_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            header_frame,
            text="Health Compliance & Immunizations",
            font=self.font_heading,
            text_color=TEXT_MAIN
        ).pack(
            side="left"
        )

        ctk.CTkLabel(
            header_frame,
            text="2025–2026 Academic Year",
            font=self.font_body,
            text_color=TEXT_LIGHT
        ).pack(
            side="right"
        )

        # ----------------------------------------------------
        # TOOLBAR
        # ----------------------------------------------------

        toolbar = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        toolbar.pack(
            fill="x",
            pady=(0, 15)
        )

        ctk.CTkButton(
            toolbar,
            text="+ Add Compliance Requirement",
            width=210,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=self._open_add_compliance
        ).pack(
            side="left"
        )

        ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=100,
            fg_color=CARD_BG,
            text_color=TEXT_MAIN,
            hover_color=SIDEBAR_BG,
            command=self._refresh_compliance
        ).pack(
            side="right"
        )

        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

        stats_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        stats_frame.pack(
            fill="x",
            pady=(0, 20)
        )

        stats_frame.grid_columnconfigure(
            (0, 1, 2),
            weight=1,
            uniform="col"
        )

        self.lbl_stat_compliant = (
            self._build_stat_card(
                stats_frame,
                0,
                "Fully Compliant",
                "0%",
                SUCCESS
            )
        )

        self.lbl_stat_missing = (
            self._build_stat_card(
                stats_frame,
                1,
                "Missing Requirements",
                "0",
                WARNING
            )
        )

        self.lbl_stat_expired = (
            self._build_stat_card(
                stats_frame,
                2,
                "Expired Action Plans",
                "0",
                DANGER
            )
        )

        ctk.CTkLabel(
            frame,
            text="Action Required",
            font=self.font_bold,
            text_color=TEXT_MAIN
        ).pack(
            anchor="w",
            pady=(10, 5)
        )

        self.comp_table = ctk.CTkScrollableFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12
        )

        self.comp_table.pack(
            fill="both",
            expand=True
        )

        self.comp_table.grid_columnconfigure(
            (0, 1, 2, 3, 4),
            weight=1
        )

        return frame

    # ========================================================
    # STAT CARD
    # ========================================================

    def _build_stat_card(
        self,
        parent,
        col,
        title,
        initial_val,
        color
    ):

        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=12
        )

        card.grid(
            row=0,
            column=col,
            sticky="nsew",
            padx=5
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=(
                "Segoe UI",
                12,
                "bold"
            ),
            text_color=TEXT_LIGHT
        ).pack(
            pady=(15, 0)
        )

        lbl_val = ctk.CTkLabel(
            card,
            text=initial_val,
            font=(
                "Segoe UI",
                28,
                "bold"
            ),
            text_color=color
        )

        lbl_val.pack(
            pady=(0, 15)
        )

        return lbl_val

    # ========================================================
    # ADD COMPLIANCE REQUIREMENT
    # ========================================================

    def _open_add_compliance(self):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Add Compliance Requirement"
        )

        dlg.geometry(
            "470x430"
        )

        dlg.grab_set()

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                last_name,
                first_name,
                matric_no,
                level
            FROM students
            ORDER BY last_name COLLATE NOCASE,
                     first_name COLLATE NOCASE
            """
        )

        students = cursor.fetchall()

        student_map = {
            (
                f"{row[1]}, {row[2]}"
                f" — {row[3]} — {row[4]}"
            ): row[0]
            for row in students
        }

        ctk.CTkLabel(
            dlg,
            text="Student",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(20, 5)
        )

        cb_student = ctk.CTkComboBox(
            dlg,
            values=list(student_map.keys()),
            state="readonly"
        )

        cb_student.pack(
            fill="x",
            padx=20
        )

        ctk.CTkLabel(
            dlg,
            text="Missing Requirement",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(15, 5)
        )

        requirement_entry = ctk.CTkEntry(
            dlg,
            placeholder_text="e.g. Vaccination record"
        )

        requirement_entry.pack(
            fill="x",
            padx=20
        )

        ctk.CTkLabel(
            dlg,
            text="Deadline (YYYY-MM-DD)",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(15, 5)
        )

        deadline_entry = ctk.CTkEntry(
            dlg,
            placeholder_text="2026-09-30"
        )

        deadline_entry.pack(
            fill="x",
            padx=20
        )

        err_lbl = ctk.CTkLabel(
            dlg,
            text="",
            text_color=DANGER,
            wraplength=400
        )

        err_lbl.pack(
            padx=20,
            pady=(15, 5)
        )

        if not student_map:

            err_lbl.configure(
                text="No student records are available. Add a student first."
            )

        def save_requirement():

            selected = cb_student.get().strip()
            requirement = requirement_entry.get().strip()
            deadline = deadline_entry.get().strip()

            student_id = student_map.get(selected)

            if not student_id:

                err_lbl.configure(
                    text="Please select a student."
                )

                return

            if not requirement:

                err_lbl.configure(
                    text="Please enter the missing requirement."
                )

                return

            try:

                datetime.strptime(
                    deadline,
                    "%Y-%m-%d"
                )

            except ValueError:

                err_lbl.configure(
                    text="Deadline must be in YYYY-MM-DD format."
                )

                return

            try:

                self.conn.execute(
                    """
                    INSERT INTO compliance (
                        student_id,
                        missing_item,
                        deadline
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        student_id,
                        requirement,
                        deadline
                    )
                )

                self.conn.commit()

                self._refresh_compliance()

                dlg.destroy()

            except Exception as exc:

                self.conn.rollback()

                messagebox.showerror(
                    "Compliance Error",
                    f"Could not save the compliance requirement:\n\n{exc}",
                    parent=dlg
                )

        ctk.CTkButton(
            dlg,
            text="Save Requirement",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=save_requirement
        ).pack(
            pady=15
        )

    # ========================================================
    # EDIT COMPLIANCE REQUIREMENT
    # ========================================================

    def _open_edit_compliance(
        self,
        compliance_id
    ):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Edit Compliance Requirement"
        )

        dlg.geometry(
            "470x360"
        )

        dlg.grab_set()

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                c.missing_item,
                c.deadline,
                s.last_name,
                s.first_name
            FROM compliance c
            JOIN students s
                ON c.student_id = s.id
            WHERE c.id = ?
            """,
            (compliance_id,)
        )

        record = cursor.fetchone()

        if not record:

            messagebox.showerror(
                "Error",
                "Compliance record not found.",
                parent=dlg
            )

            dlg.destroy()
            return

        missing_item, deadline, lname, fname = record

        ctk.CTkLabel(
            dlg,
            text=f"Student: {fname} {lname}",
            font=self.font_bold,
            text_color=TEXT_MAIN
        ).pack(
            pady=(20, 10)
        )

        ctk.CTkLabel(
            dlg,
            text="Missing Requirement",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 5)
        )

        requirement_entry = ctk.CTkEntry(
            dlg
        )

        requirement_entry.pack(
            fill="x",
            padx=20
        )

        requirement_entry.insert(
            0,
            missing_item
        )

        ctk.CTkLabel(
            dlg,
            text="Deadline (YYYY-MM-DD)",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(15, 5)
        )

        deadline_entry = ctk.CTkEntry(
            dlg
        )

        deadline_entry.pack(
            fill="x",
            padx=20
        )

        deadline_entry.insert(
            0,
            deadline
        )

        err_lbl = ctk.CTkLabel(
            dlg,
            text="",
            text_color=DANGER
        )

        err_lbl.pack(
            pady=10
        )

        def save_changes():

            requirement = requirement_entry.get().strip()
            new_deadline = deadline_entry.get().strip()

            if not requirement:

                err_lbl.configure(
                    text="Please enter the missing requirement."
                )

                return

            try:

                datetime.strptime(
                    new_deadline,
                    "%Y-%m-%d"
                )

            except ValueError:

                err_lbl.configure(
                    text="Deadline must be in YYYY-MM-DD format."
                )

                return

            try:

                self.conn.execute(
                    """
                    UPDATE compliance
                    SET missing_item = ?,
                        deadline = ?
                    WHERE id = ?
                    """,
                    (
                        requirement,
                        new_deadline,
                        compliance_id
                    )
                )

                self.conn.commit()

                self._refresh_compliance()

                dlg.destroy()

            except Exception as exc:

                self.conn.rollback()

                messagebox.showerror(
                    "Compliance Error",
                    f"Could not update the compliance record:\n\n{exc}",
                    parent=dlg
                )

        ctk.CTkButton(
            dlg,
            text="Save Changes",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=save_changes
        ).pack(
            pady=5
        )

    # ========================================================
    # RESOLVE COMPLIANCE REQUIREMENT
    # ========================================================

    def _resolve_compliance(
        self,
        compliance_id,
        student_name,
        requirement
    ):

        confirmed = messagebox.askyesno(
            "Mark as Resolved",
            (
                f"Mark this compliance requirement as resolved?\n\n"
                f"Student: {student_name}\n"
                f"Requirement: {requirement}\n\n"
                "The outstanding requirement will be removed "
                "from the Compliance list."
            ),
            parent=self
        )

        if not confirmed:
            return

        try:

            self.conn.execute(
                "DELETE FROM compliance WHERE id = ?",
                (compliance_id,)
            )

            self.conn.commit()

            self._refresh_compliance()

        except Exception as exc:

            self.conn.rollback()

            messagebox.showerror(
                "Compliance Error",
                f"Could not mark the requirement as resolved:\n\n{exc}",
                parent=self
            )

    # ========================================================
    # DELETE COMPLIANCE REQUIREMENT
    # ========================================================

    def _delete_compliance(
        self,
        compliance_id,
        student_name,
        requirement
    ):

        confirmed = messagebox.askyesno(
            "Delete Compliance Record",
            (
                f"Delete this compliance record permanently?\n\n"
                f"Student: {student_name}\n"
                f"Requirement: {requirement}"
            ),
            parent=self
        )

        if not confirmed:
            return

        try:

            self.conn.execute(
                "DELETE FROM compliance WHERE id = ?",
                (compliance_id,)
            )

            self.conn.commit()

            self._refresh_compliance()

        except Exception as exc:

            self.conn.rollback()

            messagebox.showerror(
                "Compliance Error",
                f"Could not delete the compliance record:\n\n{exc}",
                parent=self
            )

    # ========================================================
    # REFRESH COMPLIANCE
    # ========================================================

    def _refresh_compliance(self):

        if not hasattr(
            self,
            "comp_table"
        ):
            return

        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM students"
        )

        total_students = (
            cursor.fetchone()[0]
        )

        cursor.execute(
            """
            SELECT COUNT(DISTINCT student_id)
            FROM compliance
            """
        )

        students_with_issues = (
            cursor.fetchone()[0]
        )

        if total_students == 0:
            compliant_pct = 0
        else:
            compliant_pct = int(
                (
                    (
                        total_students
                        - students_with_issues
                    )
                    /
                    total_students
                )
                * 100
            )

        self.lbl_stat_compliant.configure(
            text=f"{compliant_pct}%"
        )

        cursor.execute(
            "SELECT COUNT(*) FROM compliance"
        )

        missing_count = (
            cursor.fetchone()[0]
        )

        self.lbl_stat_missing.configure(
            text=str(missing_count)
        )

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM compliance
            WHERE deadline < ?
            """,
            (today,)
        )

        expired_count = (
            cursor.fetchone()[0]
        )

        self.lbl_stat_expired.configure(
            text=str(expired_count)
        )

        for widget in self.comp_table.winfo_children():
            widget.destroy()

        headers = [
            "STUDENT",
            "LEVEL",
            "MISSING REQUIREMENT",
            "DEADLINE",
            "ACTION"
        ]

        for col, text in enumerate(headers):

            ctk.CTkLabel(
                self.comp_table,
                text=text,
                font=(
                    "Segoe UI",
                    11,
                    "bold"
                ),
                text_color=TEXT_LIGHT
            ).grid(
                row=0,
                column=col,
                sticky="w",
                padx=10,
                pady=(10, 5)
            )

        query = """
            SELECT
                c.id,
                s.last_name,
                s.first_name,
                s.level,
                c.missing_item,
                c.deadline
            FROM compliance c
            JOIN students s
                ON c.student_id = s.id
            ORDER BY c.deadline ASC,
                     s.last_name COLLATE NOCASE
        """

        cursor.execute(query)

        issues = cursor.fetchall()

        if not issues:

            ctk.CTkLabel(
                self.comp_table,
                text="No outstanding compliance requirements.",
                font=self.font_body,
                text_color=SUCCESS
            ).grid(
                row=1,
                column=0,
                columnspan=5,
                pady=30
            )

            return

        for row_idx, row in enumerate(
            issues,
            start=1
        ):

            (
                cid,
                lname,
                fname,
                level,
                missing,
                deadline
            ) = row

            student_name = f"{fname} {lname}"

            ctk.CTkLabel(
                self.comp_table,
                text=f"{lname}, {fname}",
                font=self.font_bold,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=0,
                sticky="w",
                padx=10,
                pady=10
            )

            ctk.CTkLabel(
                self.comp_table,
                text=level,
                font=self.font_body,
                text_color=TEXT_MAIN
            ).grid(
                row=row_idx,
                column=1,
                sticky="w",
                padx=10,
                pady=10
            )

            pill = ctk.CTkLabel(
                self.comp_table,
                text=f" {missing} ",
                fg_color=ALERT_PILL_BG,
                text_color=ALERT_PILL_FG,
                corner_radius=12
            )

            pill.grid(
                row=row_idx,
                column=2,
                sticky="w",
                padx=10,
                pady=10
            )

            color = (
                DANGER
                if deadline < today
                else TEXT_MAIN
            )

            ctk.CTkLabel(
                self.comp_table,
                text=deadline,
                font=self.font_body,
                text_color=color
            ).grid(
                row=row_idx,
                column=3,
                sticky="w",
                padx=10,
                pady=10
            )

            action_frame = ctk.CTkFrame(
                self.comp_table,
                fg_color="transparent"
            )

            action_frame.grid(
                row=row_idx,
                column=4,
                sticky="w",
                padx=5,
                pady=5
            )

            ctk.CTkButton(
                action_frame,
                text="Email Parent",
                width=105,
                fg_color=PRIMARY,
                hover_color=PRIMARY_HOVER,
                text_color="white",
                corner_radius=20,
                command=lambda n=student_name,
                               m=missing:
                    self._email_parent_dialog(
                        n,
                        m
                    )
            ).pack(
                side="left",
                padx=2
            )

            ctk.CTkButton(
                action_frame,
                text="Edit",
                width=55,
                fg_color=SIDEBAR_BG,
                hover_color=PRIMARY_HOVER,
                text_color=TEXT_MAIN,
                corner_radius=20,
                command=lambda item_id=cid:
                    self._open_edit_compliance(
                        item_id
                    )
            ).pack(
                side="left",
                padx=2
            )

            ctk.CTkButton(
                action_frame,
                text="Resolve",
                width=70,
                fg_color=SUCCESS,
                hover_color="#059669",
                text_color="white",
                corner_radius=20,
                command=lambda item_id=cid,
                               n=student_name,
                               m=missing:
                    self._resolve_compliance(
                        item_id,
                        n,
                        m
                    )
            ).pack(
                side="left",
                padx=2
            )

            ctk.CTkButton(
                action_frame,
                text="Delete",
                width=55,
                fg_color=DANGER,
                hover_color="#b91c1c",
                text_color="white",
                corner_radius=20,
                command=lambda item_id=cid,
                               n=student_name,
                               m=missing:
                    self._delete_compliance(
                        item_id,
                        n,
                        m
                    )
            ).pack(
                side="left",
                padx=2
            )

    # ========================================================
    # SETTINGS VIEW
    # ========================================================

    def _build_settings_view(self):

        frame = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )

        header_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        header_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            header_frame,
            text="System Settings",
            font=self.font_heading,
            text_color=TEXT_MAIN
        ).pack(side="left")

        self.save_confirm_lbl = ctk.CTkLabel(
            header_frame,
            text="",
            font=self.font_bold,
            text_color=SUCCESS
        )
        self.save_confirm_lbl.pack(side="left", padx=20)

        ctk.CTkButton(
            header_frame,
            text="Save Changes",
            font=self.font_bold,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            corner_radius=20,
            command=self._save_settings
        ).pack(side="right")

        grid_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure(
            (0, 1), weight=1, uniform="col"
        )

        # ----------------------------------------------------
        # PROFILE
        # ----------------------------------------------------

        left_card = ctk.CTkFrame(
            grid_frame, fg_color=CARD_BG, corner_radius=16
        )
        left_card.grid(
            row=0, column=0, sticky="nsew", padx=(0, 10)
        )

        ctk.CTkLabel(
            left_card, text="My Profile",
            font=self.font_bold, text_color=TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(20, 15))

        self.set_name = self._add_form_field(
            left_card, "Full Name"
        )
        self.set_email = self._add_form_field(
            left_card, "School Email"
        )
        self.set_phone = self._add_form_field(
            left_card, "Clinic Phone"
        )

        ctk.CTkLabel(
            left_card, text="Role / Position",
            font=self.font_body, text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=20, pady=(10, 0))

        self.set_position = ctk.CTkEntry(
            left_card, width=300, corner_radius=20
        )
        self.set_position.pack(
            anchor="w", padx=20, pady=(5, 10)
        )
        self.set_position.configure(state="disabled")

        ctk.CTkButton(
            left_card,
            text="Change Password",
            fg_color="transparent",
            border_width=1,
            border_color=PRIMARY,
            text_color=PRIMARY,
            command=self._change_password_dialog
        ).pack(anchor="w", padx=20, pady=(0, 10))

        if get_staff_position(self.logged_in_user) == "admin":
            ctk.CTkButton(
                left_card,
                text="Manage Staff Accounts",
                fg_color=PRIMARY,
                hover_color=PRIMARY_HOVER,
                command=self._open_manage_staff
            ).pack(anchor="w", padx=20, pady=(0, 20))

        # ----------------------------------------------------
        # NOTIFICATIONS & PRIVACY
        # ----------------------------------------------------

        right_card = ctk.CTkFrame(
            grid_frame, fg_color=CARD_BG, corner_radius=16
        )
        right_card.grid(
            row=0, column=1, sticky="nsew", padx=(10, 0)
        )

        ctk.CTkLabel(
            right_card, text="Notifications & Privacy",
            font=self.font_bold, text_color=TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(20, 15))

        # FERPA is a clinic-wide policy. Staff cannot turn it off.
        self.var_ferpa = ctk.IntVar(value=1)
        ctk.CTkCheckBox(
            right_card,
            text="FERPA Screen Lock (3 mins) — Required",
            variable=self.var_ferpa,
            text_color=TEXT_MAIN,
            state="disabled"
        ).pack(anchor="w", padx=20, pady=10)

        # Notification preferences are stored per staff account.
        self.var_teacher = ctk.IntVar(value=0)
        self.var_principal = ctk.IntVar(value=0)

        ctk.CTkCheckBox(
            right_card,
            text="Notify Teachers when student returns",
            variable=self.var_teacher,
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=10)

        ctk.CTkCheckBox(
            right_card,
            text="CC Principal on severe incidents",
            variable=self.var_principal,
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=10)

        ctk.CTkLabel(
            right_card,
            text="Default Notification Method:",
            text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=20, pady=(20, 0))

        self.set_method = ctk.CTkComboBox(
            right_card,
            values=["Email Only", "SMS Only", "Email & SMS"],
            corner_radius=20,
            state="readonly"
        )
        self.set_method.pack(anchor="w", padx=20, pady=10)

        self._load_settings()
        return frame

    # ========================================================
    # FORM FIELD
    # ========================================================

    def _add_form_field(
        self,
        parent,
        label_text
    ):

        ctk.CTkLabel(
            parent,
            text=label_text,
            font=self.font_body,
            text_color=TEXT_LIGHT
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 0)
        )

        entry = ctk.CTkEntry(
            parent,
            width=300,
            corner_radius=20
        )

        entry.pack(
            anchor="w",
            padx=20,
            pady=(5, 10)
        )

        return entry

    # ========================================================
    # LOAD SETTINGS
    # ========================================================

    def _load_settings(self):

        if not self.logged_in_user:
            return

        staff_pk = self.logged_in_user.get("id")
        if not staff_pk:
            return

        cursor = self.conn.cursor()

        # Profile values come directly from the logged-in staff row.
        cursor.execute(
            """
            SELECT surname, other_names, phone, email, position
            FROM staff
            WHERE id=?
            """,
            (staff_pk,)
        )
        staff_row = cursor.fetchone()
        if not staff_row:
            return

        surname, other_names, phone, email, position = staff_row

        full_name = " ".join(
            part
            for part in [
                str(other_names or "").strip(),
                str(surname or "").strip()
            ]
            if part
        )

        self.set_name.delete(0, "end")
        self.set_name.insert(0, full_name)

        self.set_email.delete(0, "end")
        self.set_email.insert(0, email or "")

        self.set_phone.delete(0, "end")
        self.set_phone.insert(0, phone or "")

        self.set_position.configure(state="normal")
        self.set_position.delete(0, "end")
        self.set_position.insert(0, str(position or "").title())
        self.set_position.configure(state="disabled")

        # Each staff member has an independent preference row.
        cursor.execute(
            """
            SELECT notify_teacher, cc_principal, notify_method
            FROM staff_preferences
            WHERE staff_id=?
            """,
            (staff_pk,)
        )
        pref_row = cursor.fetchone()

        if not pref_row:
            cursor.execute(
                """
                INSERT INTO staff_preferences (
                    staff_id, notify_teacher, cc_principal, notify_method
                )
                VALUES (?, 0, 0, 'Email Only')
                """,
                (staff_pk,)
            )
            self.conn.commit()
            pref_row = (0, 0, "Email Only")

        notify_teacher, cc_principal, notify_method = pref_row

        self.var_teacher.set(int(notify_teacher or 0))
        self.var_principal.set(int(cc_principal or 0))

        method = notify_method or "Email Only"
        if method not in ["Email Only", "SMS Only", "Email & SMS"]:
            method = "Email Only"
        self.set_method.set(method)

        # FERPA is always enabled clinic-wide.
        self.var_ferpa.set(1)

    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    def _save_settings(self):

        if not self.logged_in_user:
            messagebox.showerror(
                "Settings Error",
                "No active staff session was found.",
                parent=self
            )
            return

        staff_pk = self.logged_in_user.get("id")
        if not staff_pk:
            messagebox.showerror(
                "Settings Error",
                "The current staff account could not be identified.",
                parent=self
            )
            return

        new_full_name = self.set_name.get().strip()
        new_email = self.set_email.get().strip()
        new_phone = self.set_phone.get().strip()

        if not new_full_name:
            messagebox.showerror(
                "Invalid Name", "Full name is required.", parent=self
            )
            return

        if not validate_name(new_full_name):
            messagebox.showerror(
                "Invalid Name",
                "Full name can only contain letters, spaces, apostrophes and hyphens.",
                parent=self
            )
            return

        if not validate_email(new_email):
            messagebox.showerror(
                "Invalid Email",
                "Please enter a valid email address.",
                parent=self
            )
            return

        if not validate_phone(new_phone):
            messagebox.showerror(
                "Invalid Phone Number",
                "Please enter a valid Nigerian phone number.",
                parent=self
            )
            return

        parts = new_full_name.split()
        if len(parts) >= 2:
            surname = parts[-1]
            other_names = " ".join(parts[:-1])
        else:
            surname = parts[0]
            other_names = ""

        cursor = self.conn.cursor()

        try:
            cursor.execute(
                """
                SELECT 1 FROM staff
                WHERE phone=? AND id<>?
                """,
                (new_phone, staff_pk)
            )
            if cursor.fetchone():
                messagebox.showerror(
                    "Phone Already Used",
                    "That phone number is already assigned to another staff account.",
                    parent=self
                )
                return

            if new_email:
                cursor.execute(
                    """
                    SELECT 1 FROM staff
                    WHERE email=? AND id<>?
                    """,
                    (new_email, staff_pk)
                )
                if cursor.fetchone():
                    messagebox.showerror(
                        "Email Already Used",
                        "That email address is already assigned to another staff account.",
                        parent=self
                    )
                    return

            # Role/position is intentionally NOT included in this UPDATE.
            cursor.execute(
                """
                UPDATE staff
                SET surname=?, other_names=?, email=?, phone=?
                WHERE id=?
                """,
                (
                    surname, other_names, new_email or None,
                    new_phone, staff_pk
                )
            )

            cursor.execute(
                """
                INSERT OR IGNORE INTO staff_preferences (
                    staff_id, notify_teacher, cc_principal, notify_method
                )
                VALUES (?, 0, 0, 'Email Only')
                """,
                (staff_pk,)
            )

            cursor.execute(
                """
                UPDATE staff_preferences
                SET notify_teacher=?, cc_principal=?, notify_method=?
                WHERE staff_id=?
                """,
                (
                    int(self.var_teacher.get()),
                    int(self.var_principal.get()),
                    self.set_method.get(),
                    staff_pk
                )
            )

            self.conn.commit()

            # Keep the active session synchronized. This means the same
            # current staff name is used by student registration's Added By.
            self.logged_in_user["surname"] = surname
            self.logged_in_user["other_names"] = other_names
            self.logged_in_user["email"] = new_email or None
            self.logged_in_user["phone"] = new_phone

            self.save_confirm_lbl.configure(text="Settings saved ✓")
            self.after(
                2000,
                lambda: self.save_confirm_lbl.configure(text="")
            )

        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            messagebox.showerror(
                "Settings Error",
                f"Could not save your settings:\n\n{exc}",
                parent=self
            )
        except Exception as exc:
            self.conn.rollback()
            messagebox.showerror(
                "Settings Error",
                f"Could not save your settings:\n\n{exc}",
                parent=self
            )

    # ========================================================
    # CHANGE PASSWORD
    # ========================================================

    def _change_password_dialog(self):

        self.after(
            10,
            self._open_pwd_dialog
        )

    def _open_pwd_dialog(self):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Change Password"
        )

        dlg.geometry(
            "350x380"
        )

        dlg.grab_set()

        ctk.CTkLabel(
            dlg,
            text="Current Password"
        ).pack(
            pady=(20, 5)
        )

        entry_curr = ctk.CTkEntry(
            dlg,
            show="*"
        )

        entry_curr.pack()

        ctk.CTkLabel(
            dlg,
            text="New Password"
        ).pack(
            pady=(10, 5)
        )

        entry_new = ctk.CTkEntry(
            dlg,
            show="*"
        )

        entry_new.pack()

        ctk.CTkLabel(
            dlg,
            text="Confirm New Password"
        ).pack(
            pady=(10, 5)
        )

        entry_conf = ctk.CTkEntry(
            dlg,
            show="*"
        )

        entry_conf.pack()

        err_lbl = ctk.CTkLabel(
            dlg,
            text="",
            text_color=DANGER,
            wraplength=280
        )

        err_lbl.pack(
            pady=(12, 0)
        )

        def save_pwd():

            curr = entry_curr.get()
            new = entry_new.get()
            conf = entry_conf.get()

            if not curr or not new or not conf:

                err_lbl.configure(
                    text="All fields are required."
                )

                return

            if not self.logged_in_user:

                err_lbl.configure(
                    text="No active session found."
                )

                return

            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT password_hash
                FROM staff
                WHERE staff_id=?
                """,
                (
                    self.logged_in_user[
                        "staff_id"
                    ],
                )
            )

            row = cursor.fetchone()

            if not row:

                err_lbl.configure(
                    text="Account not found."
                )

                return

            stored_hash = row[0]

            try:

                current_ok = bcrypt.checkpw(
                    curr.encode("utf-8"),
                    stored_hash.encode("utf-8")
                )

            except (
                ValueError,
                AttributeError
            ):

                current_ok = (
                    hashlib.sha256(
                        curr.encode()
                    ).hexdigest()
                    == stored_hash
                )

            if not current_ok:

                err_lbl.configure(
                    text="Current password is incorrect."
                )

                return

            if len(new) < 6:

                err_lbl.configure(
                    text="New password must be at least 6 characters."
                )

                return

            if new != conf:

                err_lbl.configure(
                    text="New passwords do not match."
                )

                return

            if new == curr:

                err_lbl.configure(
                    text="New password must be different from the current one."
                )

                return

            new_hash = bcrypt.hashpw(
                new.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            self.conn.execute(
                """
                UPDATE staff
                SET password_hash=?
                WHERE staff_id=?
                """,
                (
                    new_hash,
                    self.logged_in_user[
                        "staff_id"
                    ]
                )
            )

            self.conn.commit()

            self.logged_in_user[
                "password_hash"
            ] = new_hash

            messagebox.showinfo(
                "Success",
                "Password updated successfully.",
                parent=dlg
            )

            dlg.destroy()

        ctk.CTkButton(
            dlg,
            text="Save Password",
            command=save_pwd,
            fg_color=PRIMARY
        ).pack(
            pady=20
        )

        dlg.bind(
            "<Return>",
            lambda e: save_pwd()
        )

    # ========================================================
    # FERPA SCREEN LOCK
    # ========================================================

    def _reset_activity(
        self,
        event=None
    ):

        self.last_activity = time.time()

    def _check_idle(self):

        # FERPA locking is enforced for every logged-in staff member.
        if self.ferpa_enabled and not self._locked:

            if (
                time.time()
                - self.last_activity
                >= FERPA_LOCK_SECONDS
            ):

                self._lock_screen()

        self.after(
            5000,
            self._check_idle
        )

    def _lock_screen(self):

        if self._locked:
            return

        self._locked = True

        self.lock_dlg = ctk.CTkToplevel(
            self
        )

        self.lock_dlg.title(
            "Session Locked"
        )

        self.lock_dlg.geometry(
            "400x300"
        )

        self.lock_dlg.protocol(
            "WM_DELETE_WINDOW",
            lambda: None
        )

        self.lock_dlg.grab_set()

        self.lock_dlg.attributes(
            "-topmost",
            True
        )

        ctk.CTkLabel(
            self.lock_dlg,
            text="Session Locked",
            font=self.font_heading,
            text_color=TEXT_MAIN
        ).pack(
            pady=(35, 10)
        )

        ctk.CTkLabel(
            self.lock_dlg,
            text=(
                "FERPA privacy timeout — please re-enter your\n"
                "password to continue."
            ),
            text_color=TEXT_LIGHT,
            justify="center"
        ).pack(
            pady=(0, 20)
        )

        entry_pw = ctk.CTkEntry(
            self.lock_dlg,
            show="*",
            placeholder_text="Password",
            width=250
        )

        entry_pw.pack(
            pady=5
        )

        err_lbl = ctk.CTkLabel(
            self.lock_dlg,
            text="",
            text_color=DANGER
        )

        err_lbl.pack(
            pady=(5, 0)
        )

        def try_unlock():

            if not self.logged_in_user:

                err_lbl.configure(
                    text="No active session found."
                )

                return

            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT password_hash
                FROM staff
                WHERE staff_id=?
                """,
                (
                    self.logged_in_user[
                        "staff_id"
                    ],
                )
            )

            row = cursor.fetchone()

            stored_hash = (
                row[0]
                if row
                else None
            )

            ok = False

            if stored_hash:

                try:

                    ok = bcrypt.checkpw(
                        entry_pw.get().encode(
                            "utf-8"
                        ),
                        stored_hash.encode(
                            "utf-8"
                        )
                    )

                except (
                    ValueError,
                    AttributeError
                ):

                    ok = (
                        hashlib.sha256(
                            entry_pw.get().encode()
                        ).hexdigest()
                        == stored_hash
                    )

            if ok:

                self._locked = False

                self.last_activity = (
                    time.time()
                )

                self.lock_dlg.grab_release()

                self.lock_dlg.destroy()

            else:

                err_lbl.configure(
                    text="Incorrect password."
                )

                entry_pw.delete(
                    0,
                    "end"
                )

        ctk.CTkButton(
            self.lock_dlg,
            text="Unlock",
            fg_color=PRIMARY,
            command=try_unlock
        ).pack(
            pady=15
        )

        self.lock_dlg.bind(
            "<Return>",
            lambda e: try_unlock()
        )

        entry_pw.focus_set()

    # ========================================================
    # ADD STUDENT
    # ========================================================

    def _add_student_dialog(self):

        self.after(
            10,
            self._open_add_student
        )

    def _open_add_student(self):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Add New Student"
        )

        dlg.geometry(
            "480x900"
        )

        dlg.grab_set()

        scroll = ctk.CTkScrollableFrame(
            dlg,
            fg_color="transparent"
        )

        scroll.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        fields = {}

        # ====================================================
        # FIELD HELPERS
        # ====================================================

        def add_entry(
            label,
            placeholder=""
        ):

            ctk.CTkLabel(
                scroll,
                text=label,
                anchor="w"
            ).pack(
                fill="x",
                pady=(5, 0)
            )

            entry = ctk.CTkEntry(
                scroll,
                placeholder_text=placeholder
            )

            entry.pack(
                fill="x",
                pady=(0, 5)
            )

            fields[label] = entry

            return entry

        def add_combo(
            label,
            values,
            default=None
        ):

            ctk.CTkLabel(
                scroll,
                text=label,
                anchor="w"
            ).pack(
                fill="x",
                pady=(5, 0)
            )

            combo = ctk.CTkComboBox(
                scroll,
                values=values,
                state="readonly"
            )

            combo.pack(
                fill="x",
                pady=(0, 5)
            )

            if default:
                combo.set(
                    default
                )

            fields[label] = combo

            return combo

        # ====================================================
        # STUDENT INFORMATION
        # ====================================================

        last_name_entry = add_entry(
            "Last Name"
        )

        first_name_entry = add_entry(
            "First Name"
        )

        matric_entry = add_entry(
            "Matric No."
        )

        # ----------------------------------------------------
        # MATRIC NUMBER LIVE FORMAT
        # ----------------------------------------------------

        matric_error_lbl = ctk.CTkLabel(
            scroll,
            text=(
                "Required format: "
                "ADUN/FS/SEN/22/001"
            ),
            text_color=TEXT_LIGHT,
            font=(
                "Segoe UI",
                11
            )
        )

        matric_error_lbl.pack(
            fill="x",
            pady=(0, 5)
        )

        add_combo(
            "Level",
            LEVEL_OPTIONS,
            LEVEL_OPTIONS[0]
        )

        # ====================================================
        # DEPARTMENT
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="Department",
            anchor="w"
        ).pack(
            fill="x",
            pady=(5, 0)
        )

        department_entry = ctk.CTkEntry(
            scroll
        )

        department_entry.pack(
            fill="x",
            pady=(0, 5)
        )

        department_entry.configure(
            state="disabled"
        )

        fields[
            "Department"
        ] = department_entry

        # ====================================================
        # AUTO DEPARTMENT
        # ====================================================

        def update_department(
            event=None
        ):

            matric_no = (
                matric_entry
                .get()
                .strip()
                .upper()
            )

            department_entry.configure(
                state="normal"
            )

            department_entry.delete(
                0,
                "end"
            )

            if validate_matric_number(
                matric_no
            ):

                department = (
                    get_department_from_matric(
                        matric_no
                    )
                )

                if department:

                    department_entry.insert(
                        0,
                        department
                    )

                    matric_error_lbl.configure(
                        text="Valid matric number ✓",
                        text_color=SUCCESS
                    )

            else:

                matric_error_lbl.configure(
                    text=(
                        "Required format: "
                        "ADUN/FS/SEN/22/001"
                    ),
                    text_color=TEXT_LIGHT
                )

            department_entry.configure(
                state="disabled"
            )

        matric_entry.bind(
            "<KeyRelease>",
            update_department
        )

        # ====================================================
        # HEALTH INFORMATION
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="Medical Information",
            font=self.font_bold,
            text_color=TEXT_MAIN
        ).pack(
            fill="x",
            pady=(15, 5)
        )

        add_combo(
            "Blood Group",
            BLOOD_GROUP_OPTIONS,
            BLOOD_GROUP_OPTIONS[0]
        )

        add_combo(
            "Genotype",
            GENOTYPE_OPTIONS,
            GENOTYPE_OPTIONS[0]
        )

        add_combo(
            "Rhesus Factor",
            RHESUS_OPTIONS,
            RHESUS_OPTIONS[0]
        )

        add_combo(
            "Are Your Vaccines Up To Date?",
            VACCINE_OPTIONS,
            "NO"
        )

        add_entry(
            "Health Conditions (comma-separated)",
            "e.g. Asthma, Migraine, Allergy"
        )

        # ====================================================
        # EMERGENCY CONTACT
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="Emergency Contact",
            font=self.font_bold,
            text_color=TEXT_MAIN
        ).pack(
            fill="x",
            pady=(15, 5)
        )

        add_entry(
            "Emergency Contact Name"
        )

        add_combo(
            "Relationship",
            RELATIONSHIP_OPTIONS,
            "Mother"
        )

        add_entry(
            "Phone"
        )

        # ====================================================
        # ADDED BY
        # ====================================================

        ctk.CTkLabel(
            scroll,
            text="Added By",
            anchor="w"
        ).pack(
            fill="x",
            pady=(15, 0)
        )

        added_by_entry = ctk.CTkEntry(
            scroll
        )

        # ----------------------------------------------------
        # FIX FOR "ADDED BY"
        #
        # This is derived from the logged-in account rather
        # than manually entered.
        # ----------------------------------------------------

        logged_staff_name = (
            get_staff_display_name(
                self.logged_in_user
            )
        )

        added_by_entry.insert(
            0,
            logged_staff_name
        )

        added_by_entry.configure(
            state="disabled"
        )

        added_by_entry.pack(
            fill="x",
            pady=(0, 5)
        )

        fields[
            "Added By"
        ] = added_by_entry

        # ====================================================
        # SUBMIT
        # ====================================================

        def submit():

            matric_no = (
                matric_entry
                .get()
                .strip()
                .upper()
            )

            last_name = (
                last_name_entry
                .get()
                .strip()
            )

            first_name = (
                first_name_entry
                .get()
                .strip()
            )

            emergency_name = (
                fields[
                    "Emergency Contact Name"
                ]
                .get()
                .strip()
            )

            emergency_phone = (
                fields[
                    "Phone"
                ]
                .get()
                .strip()
            )

            relationship = (
                fields[
                    "Relationship"
                ].get()
            )

            # ------------------------------------------------
            # REQUIRED FIELD VALIDATION
            # ------------------------------------------------

            if not last_name:

                messagebox.showerror(
                    "Missing Information",
                    "Please enter the student's last name.",
                    parent=dlg
                )

                return

            if not validate_name(
                last_name
            ):

                messagebox.showerror(
                    "Invalid Last Name",
                    "Last name can only contain letters, spaces, apostrophes and hyphens.",
                    parent=dlg
                )

                return

            if not first_name:

                messagebox.showerror(
                    "Missing Information",
                    "Please enter the student's first name.",
                    parent=dlg
                )

                return

            if not validate_name(
                first_name
            ):

                messagebox.showerror(
                    "Invalid First Name",
                    "First name can only contain letters, spaces, apostrophes and hyphens.",
                    parent=dlg
                )

                return

            # ------------------------------------------------
            # MATRIC VALIDATION
            # ------------------------------------------------

            if not validate_matric_number(
                matric_no
            ):

                messagebox.showerror(
                    "Invalid Matric Number",
                    (
                        "Please enter a valid ADUN matric number.\n\n"
                        "Required format:\n"
                        "ADUN/FS/SEN/22/001\n\n"
                        "Examples:\n"
                        "ADUN/FS/SEN/22/001\n"
                        "ADUN/FS/FRS/22/002\n"
                        "ADUN/FS/CYB/23/003"
                    ),
                    parent=dlg
                )

                return

            # ------------------------------------------------
            # DEPARTMENT
            # ------------------------------------------------

            department = (
                get_department_from_matric(
                    matric_no
                )
            )

            if not department:

                messagebox.showerror(
                    "Invalid Department",
                    (
                        "The department code in the matric "
                        "number is not recognised."
                    ),
                    parent=dlg
                )

                return

            # ------------------------------------------------
            # PHONE
            # ------------------------------------------------

            if not validate_phone(
                emergency_phone
            ):

                messagebox.showerror(
                    "Invalid Phone Number",
                    (
                        "Please enter a valid Nigerian "
                        "phone number."
                    ),
                    parent=dlg
                )

                return

            # ------------------------------------------------
            # EMERGENCY CONTACT
            # ------------------------------------------------

            if not emergency_name:

                messagebox.showerror(
                    "Missing Emergency Contact",
                    "Please enter an emergency contact name.",
                    parent=dlg
                )

                return

            if not validate_name(
                emergency_name
            ):

                messagebox.showerror(
                    "Invalid Contact Name",
                    "Emergency contact name contains invalid characters.",
                    parent=dlg
                )

                return

            # ------------------------------------------------
            # DATABASE INSERT
            # ------------------------------------------------

            try:

                cursor = self.conn.cursor()

                # --------------------------------------------
                # Added By is taken directly from session.
                # --------------------------------------------

                added_by = (
                    get_staff_display_name(
                        self.logged_in_user
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO students (
                        matric_no,
                        last_name,
                        first_name,
                        level,
                        department,
                        blood_group,
                        genotype,
                        rhesus_factor,
                        vaccines_up_to_date,
                        added_by
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        matric_no,
                        last_name,
                        first_name,
                        fields[
                            "Level"
                        ].get(),
                        department,
                        fields[
                            "Blood Group"
                        ].get(),
                        fields[
                            "Genotype"
                        ].get(),
                        fields[
                            "Rhesus Factor"
                        ].get(),
                        fields[
                            "Are Your Vaccines Up To Date?"
                        ].get(),
                        added_by
                    )
                )

                student_id_db = (
                    cursor.lastrowid
                )

                # --------------------------------------------
                # EMERGENCY CONTACT
                # --------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO emergency_contacts (
                        student_id,
                        contact_name,
                        relationship,
                        phone
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        student_id_db,
                        emergency_name,
                        relationship,
                        emergency_phone
                    )
                )

                # --------------------------------------------
                # HEALTH CONDITIONS
                # --------------------------------------------

                condition_text = (
                    fields[
                        "Health Conditions (comma-separated)"
                    ].get()
                )

                conditions = (
                    condition_text.split(",")
                )

                for condition in conditions:

                    condition = (
                        condition.strip()
                    )

                    if condition:

                        cursor.execute(
                            """
                            INSERT INTO health_conditions (
                                student_id,
                                condition
                            )
                            VALUES (?, ?)
                            """,
                            (
                                student_id_db,
                                condition
                            )
                        )

                self.conn.commit()

                # Update condition filter immediately.
                self._refresh_condition_filter_options()

                self._refresh_directory()

                dlg.destroy()

                messagebox.showinfo(
                    "Student Registered",
                    (
                        f"{first_name} {last_name} "
                        "has been registered successfully."
                    )
                )

            except sqlite3.IntegrityError:

                self.conn.rollback()

                messagebox.showerror(
                    "Registration Error",
                    "Matric No. already exists.",
                    parent=dlg
                )

            except Exception as exc:

                self.conn.rollback()

                messagebox.showerror(
                    "Registration Error",
                    (
                        "An error occurred while registering "
                        f"the student:\n\n{exc}"
                    ),
                    parent=dlg
                )

        # ====================================================
        # SAVE BUTTON
        # ====================================================

        ctk.CTkButton(
            scroll,
            text="Save Student",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            height=45,
            command=submit
        ).pack(
            pady=20
        )

    # ========================================================
    # LOG VISIT
    # ========================================================

    def _log_visit_dialog(self):

        self.after(
            10,
            self._open_log_visit
        )

    def _open_log_visit(self):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Log Clinic Visit"
        )

        dlg.geometry(
            "450x700"
        )

        dlg.grab_set()

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                last_name,
                first_name
            FROM students
            ORDER BY last_name COLLATE NOCASE
            """
        )

        students = cursor.fetchall()

        stu_map = {
            f"{r[1]}, {r[2]}": r[0]
            for r in students
        }

        # ----------------------------------------------------
        # STUDENT
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Student",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(15, 0)
        )

        cb_student = ctk.CTkComboBox(
            dlg,
            values=list(
                stu_map.keys()
            ),
            state="readonly"
        )

        cb_student.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Time (YYYY-MM-DD HH:MM)",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 0)
        )

        en_time = ctk.CTkEntry(
            dlg
        )

        en_time.insert(
            0,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        en_time.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # REASON / AILMENT
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Ailment / Reason for Visit",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 0)
        )

        en_reason = ctk.CTkEntry(
            dlg,
            placeholder_text="e.g. Headache, Fever, Stomachache"
        )

        en_reason.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # TREATMENT
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Treatment / Action Taken",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 0)
        )

        en_treatment = ctk.CTkEntry(
            dlg,
            placeholder_text="e.g. Rest, water, first aid"
        )

        en_treatment.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # DRUG ADMINISTERED
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Drug Administered",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 0)
        )

        en_drug = ctk.CTkEntry(
            dlg,
            placeholder_text="e.g. Paracetamol 500mg"
        )

        en_drug.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # DRUG STATUS
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Drug Status",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 0)
        )

        cb_drug_status = ctk.CTkComboBox(
            dlg,
            values=DRUG_STATUS_OPTIONS,
            state="readonly"
        )

        cb_drug_status.set(
            "No Drug Required"
        )

        cb_drug_status.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # AUTO CLEAR DRUG NAME WHEN NO DRUG
        # ----------------------------------------------------

        def drug_status_changed(value):

            if value in (
                "No Drug Required",
                "Advised to Buy Elsewhere"
            ):

                if value == "No Drug Required":

                    en_drug.delete(
                        0,
                        "end"
                    )

                elif value == "Advised to Buy Elsewhere":

                    en_drug.delete(
                        0,
                        "end"
                    )

                    en_drug.insert(
                        0,
                        "Not administered at clinic"
                    )

        cb_drug_status.configure(
            command=drug_status_changed
        )

        # ----------------------------------------------------
        # DISPOSITION
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text="Disposition",
            anchor="w"
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 0)
        )

        cb_disp = ctk.CTkComboBox(
            dlg,
            values=DISPOSITION_OPTIONS,
            state="readonly"
        )

        cb_disp.set(
            "Returned to Class"
        )

        cb_disp.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # ERROR LABEL
        # ----------------------------------------------------

        err_lbl = ctk.CTkLabel(
            dlg,
            text="",
            text_color=DANGER,
            wraplength=380
        )

        err_lbl.pack(
            padx=20
        )

        # ----------------------------------------------------
        # SUBMIT
        # ----------------------------------------------------

        def submit():

            sid = stu_map.get(
                cb_student.get()
            )

            if not sid:

                err_lbl.configure(
                    text="Please select a student."
                )

                return

            if not en_reason.get().strip():

                err_lbl.configure(
                    text="Please enter the ailment/reason."
                )

                return

            if not en_treatment.get().strip():

                err_lbl.configure(
                    text="Please enter the treatment/action taken."
                )

                return

            if not cb_disp.get():

                err_lbl.configure(
                    text="Please select a disposition."
                )

                return

            student_display = (
                cb_student.get()
            )

            disp = cb_disp.get()

            drug = (
                en_drug.get().strip()
            )

            drug_status = (
                cb_drug_status.get().strip()
            )

            # ----------------------------------------------
            # Drug consistency checks
            # ----------------------------------------------

            if drug_status == "Administered at Clinic":

                if not drug:

                    err_lbl.configure(
                        text=(
                            "Please enter the drug administered."
                        )
                    )

                    return

            if drug_status == "Prescribed":

                if not drug:

                    err_lbl.configure(
                        text=(
                            "Please enter the prescribed drug."
                        )
                    )

                    return

            if drug_status == "Advised to Buy Elsewhere":

                drug = (
                    drug
                    or "Not administered at clinic"
                )

            if drug_status == "No Drug Required":

                drug = ""

            # ----------------------------------------------
            # SAVE
            # ----------------------------------------------

            try:

                self.conn.execute(
                    """
                    INSERT INTO visit_logs (
                        student_id,
                        visit_time,
                        reason,
                        treatment,
                        drug_administered,
                        drug_status,
                        disposition
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sid,
                        en_time.get().strip(),
                        en_reason.get().strip(),
                        en_treatment.get().strip(),
                        drug,
                        drug_status,
                        disp
                    )
                )

                self.conn.commit()

                self._refresh_visits()

                dlg.destroy()

                # ------------------------------------------
                # NOTIFICATIONS
                # ------------------------------------------

                method = (
                    self.set_method.get()
                    if hasattr(
                        self,
                        "set_method"
                    )
                    else "Email & SMS"
                )

                notices = []

                if (
                    disp == "Returned to Class"
                    and self.var_teacher.get() == 1
                ):

                    notices.append(
                        (
                            f"Teacher notified via {method}: "
                            f"{student_display} has returned to class."
                        )
                    )

                if (
                    disp == "911 / Emergency"
                    and self.var_principal.get() == 1
                ):

                    notices.append(
                        (
                            f"Principal's office CC'd via "
                            f"{method} on this emergency "
                            f"incident involving "
                            f"{student_display}."
                        )
                    )

                if notices:

                    messagebox.showinfo(
                        "Notifications Sent",
                        "\n\n".join(notices)
                    )

            except Exception as exc:

                self.conn.rollback()

                messagebox.showerror(
                    "Error",
                    f"Could not save visit:\n\n{exc}",
                    parent=dlg
                )

        ctk.CTkButton(
            dlg,
            text="Save Visit",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            command=submit
        ).pack(
            pady=10
        )

    # ========================================================
    # EMAIL PARENT
    # ========================================================

    def _email_parent_dialog(
        self,
        student_name,
        missing_item
    ):

        self.after(
            10,
            lambda:
                self._open_email_parent(
                    student_name,
                    missing_item
                )
        )

    def _open_email_parent(
        self,
        student_name,
        missing_item
    ):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Draft Email Notification"
        )

        dlg.geometry(
            "500x350"
        )

        dlg.grab_set()

        ctk.CTkLabel(
            dlg,
            text=f"Regarding: {student_name}",
            font=self.font_bold
        ).pack(
            pady=(10, 5)
        )

        cc_line = ""

        if (
            hasattr(
                self,
                "var_principal"
            )
            and self.var_principal.get() == 1
        ):

            cc_line = (
                "CC: Principal's Office\n"
            )

        msg = (
            f"Dear Parent/Guardian,\n\n"
            f"{cc_line}"
            f"Our records indicate that {student_name} "
            f"is currently non-compliant regarding the "
            f"following health requirement: {missing_item}.\n\n"
            "Please provide updated documentation to the "
            "clinic as soon as possible to ensure your "
            "student may continue attending classes without "
            "interruption.\n\n"
            "Thank you,\n"
            "ClinicPortal Administration"
        )

        textbox = ctk.CTkTextbox(
            dlg,
            height=200,
            corner_radius=12
        )

        textbox.pack(
            fill="both",
            padx=20,
            pady=10
        )

        textbox.insert(
            "1.0",
            msg
        )

        def copy_close():

            self.clipboard_clear()

            self.clipboard_append(
                textbox.get(
                    "1.0",
                    "end-1c"
                )
            )

            dlg.destroy()

        ctk.CTkButton(
            dlg,
            text="Copy to Clipboard & Close",
            fg_color=PRIMARY,
            command=copy_close
        ).pack(
            pady=10
        )

    # ========================================================
    # STUDENT PROFILE
    # ========================================================

    def _view_student_profile(
        self,
        db_id
    ):

        self.after(
            10,
            lambda:
                self._open_student_profile(
                    db_id
                )
        )

    def _open_student_profile(
        self,
        db_id
    ):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Student Profile"
        )

        dlg.geometry(
            "500x750"
        )

        dlg.grab_set()

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                first_name,
                last_name,
                matric_no,
                level,
                department,
                blood_group,
                genotype,
                rhesus_factor,
                vaccines_up_to_date,
                added_by
            FROM students
            WHERE id = ?
            """,
            (db_id,)
        )

        student = cursor.fetchone()

        if not student:

            messagebox.showerror(
                "Error",
                "Student record not found.",
                parent=dlg
            )

            dlg.destroy()
            return

        (
            fname,
            lname,
            matric_no,
            level,
            department,
            blood_group,
            genotype,
            rhesus_factor,
            vaccines,
            added_by
        ) = student

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        ctk.CTkLabel(
            dlg,
            text=f"{fname} {lname}",
            font=self.font_heading,
            text_color=TEXT_MAIN
        ).pack(
            pady=(20, 10)
        )

        info_frame = ctk.CTkScrollableFrame(
            dlg,
            fg_color=CARD_BG,
            corner_radius=12
        )

        info_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # INFO ROW
        # ----------------------------------------------------

        def info_row(
            label,
            value,
            value_color=TEXT_MAIN
        ):

            row = ctk.CTkFrame(
                info_frame,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=15,
                pady=6
            )

            ctk.CTkLabel(
                row,
                text=label,
                font=self.font_bold,
                text_color=TEXT_LIGHT,
                width=160,
                anchor="w"
            ).pack(
                side="left"
            )

            ctk.CTkLabel(
                row,
                text=value or "—",
                text_color=value_color,
                anchor="w",
                wraplength=230
            ).pack(
                side="left"
            )

        # ----------------------------------------------------
        # BASIC INFORMATION
        # ----------------------------------------------------

        info_row(
            "Matric No.",
            matric_no
        )

        info_row(
            "Level",
            level
        )

        info_row(
            "Department",
            department
        )

        # ----------------------------------------------------
        # MEDICAL INFORMATION
        # ----------------------------------------------------

        info_row(
            "Blood Group",
            blood_group
        )

        info_row(
            "Genotype",
            genotype
        )

        info_row(
            "Rhesus Factor",
            rhesus_factor
        )

        info_row(
            "Vaccines Up To Date",
            vaccines,
            (
                SUCCESS
                if vaccines == "YES"
                else DANGER
            )
        )

        # ----------------------------------------------------
        # ADDED BY
        # ----------------------------------------------------

        info_row(
            "Added By",
            added_by
        )

        # ----------------------------------------------------
        # HEALTH CONDITIONS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT condition
            FROM health_conditions
            WHERE student_id = ?
            ORDER BY condition COLLATE NOCASE
            """,
            (db_id,)
        )

        conditions = [
            row[0]
            for row in cursor.fetchall()
        ]

        info_row(
            "Health Conditions",
            (
                ", ".join(conditions)
                if conditions
                else "None recorded"
            )
        )

        # ----------------------------------------------------
        # EMERGENCY CONTACT
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                contact_name,
                relationship,
                phone
            FROM emergency_contacts
            WHERE student_id = ?
            """,
            (db_id,)
        )

        contacts = cursor.fetchall()

        if contacts:

            contact_text = "\n".join(
                [
                    (
                        f"{name} — {relationship} "
                        f"— {phone}"
                    )
                    for name, relationship, phone
                    in contacts
                ]
            )

        else:

            contact_text = "No emergency contact"

        info_row(
            "Emergency Contact",
            contact_text
        )

        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        def delete_student():

            if messagebox.askyesno(
                "Confirm",
                (
                    f"Delete {fname} {lname}?\n\n"
                    "This will also delete the student's "
                    "health conditions, emergency contacts, "
                    "visit logs and compliance records."
                ),
                parent=dlg
            ):

                try:

                    self.conn.execute(
                        """
                        DELETE FROM students
                        WHERE id = ?
                        """,
                        (db_id,)
                    )

                    self.conn.commit()

                    self._refresh_condition_filter_options()

                    self._refresh_directory()

                    dlg.destroy()

                except Exception as exc:

                    self.conn.rollback()

                    messagebox.showerror(
                        "Delete Error",
                        str(exc),
                        parent=dlg
                    )

        ctk.CTkButton(
            dlg,
            text="Delete Record",
            fg_color=DANGER,
            hover_color="#b91c1c",
            command=delete_student
        ).pack(
            pady=20
        )

    # ========================================================
    # MANAGE STAFF
    # ========================================================

    def _open_manage_staff(self):

        dlg = ctk.CTkToplevel(
            self
        )

        dlg.title(
            "Manage Staff Accounts"
        )

        dlg.geometry(
            "750x600"
        )

        dlg.grab_set()

        # ----------------------------------------------------
        # TOP
        # ----------------------------------------------------

        top_frame = ctk.CTkFrame(
            dlg,
            fg_color="transparent"
        )

        top_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ctk.CTkLabel(
            top_frame,
            text="Add New Staff",
            font=(
                "Arial",
                16,
                "bold"
            )
        ).pack(
            anchor="w"
        )

        form_frame = ctk.CTkFrame(
            top_frame
        )

        form_frame.pack(
            fill="x",
            pady=5
        )

        # ----------------------------------------------------
        # SURNAME
        # ----------------------------------------------------

        surname_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Surname",
            width=110
        )

        surname_entry.grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )

        # ----------------------------------------------------
        # OTHER NAMES
        # ----------------------------------------------------

        other_names_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Other Names",
            width=130
        )

        other_names_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        # ----------------------------------------------------
        # POSITION
        # ----------------------------------------------------

        position_cbo = ctk.CTkComboBox(
            form_frame,
            values=[
                "nurse",
                "admin"
            ],
            width=100,
            state="readonly"
        )

        position_cbo.grid(
            row=0,
            column=2,
            padx=5,
            pady=5
        )

        position_cbo.set(
            "nurse"
        )

        # ----------------------------------------------------
        # STAFF ID
        # ----------------------------------------------------

        id_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="XXX-XXX-0000",
            width=130
        )

        id_entry.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        # ----------------------------------------------------
        # PHONE
        # ----------------------------------------------------

        phone_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Phone",
            width=120
        )

        phone_entry.grid(
            row=1,
            column=0,
            padx=5,
            pady=5
        )

        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        email_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Email",
            width=150
        )

        email_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        pass_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Password",
            show="*",
            width=120
        )

        pass_entry.grid(
            row=1,
            column=2,
            padx=5,
            pady=5
        )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        err_lbl = ctk.CTkLabel(
            top_frame,
            text="",
            text_color=DANGER
        )

        err_lbl.pack(
            anchor="w"
        )

        # ====================================================
        # ADD STAFF
        # ====================================================

        def add_staff():

            surname = (
                surname_entry
                .get()
                .strip()
            )

            other_names = (
                other_names_entry
                .get()
                .strip()
            )

            position = (
                position_cbo.get()
                .strip()
            )

            new_id = (
                id_entry
                .get()
                .strip()
                .upper()
            )

            phone = (
                phone_entry
                .get()
                .strip()
            )

            email = (
                email_entry
                .get()
                .strip()
            )

            new_pass = (
                pass_entry.get()
            )

            # ------------------------------------------------
            # REQUIRED FIELDS
            # ------------------------------------------------

            if not all([
                surname,
                other_names,
                position,
                new_id,
                phone,
                new_pass
            ]):

                err_lbl.configure(
                    text="All required fields must be completed."
                )

                return

            # ------------------------------------------------
            # NAME VALIDATION
            # ------------------------------------------------

            if not validate_name(
                surname
            ):

                err_lbl.configure(
                    text="Invalid surname."
                )

                return

            if not validate_name(
                other_names
            ):

                err_lbl.configure(
                    text="Invalid other names."
                )

                return

            # ------------------------------------------------
            # STAFF ID
            # ------------------------------------------------

            if not re.fullmatch(
                r"^[A-Z]{3}-[A-Z]{3}-\d{4}$",
                new_id
            ):

                err_lbl.configure(
                    text=(
                        "Staff ID must be in the "
                        "format XXX-XXX-0000."
                    )
                )

                return

            # ------------------------------------------------
            # PHONE
            # ------------------------------------------------

            if not validate_phone(
                phone
            ):

                err_lbl.configure(
                    text="Please enter a valid Nigerian phone number."
                )

                return

            # ------------------------------------------------
            # EMAIL
            # ------------------------------------------------

            if email and not (
                re.fullmatch(
                    r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$",
                    email
                )
            ):

                err_lbl.configure(
                    text="Please enter a valid email address."
                )

                return

            # ------------------------------------------------
            # PASSWORD
            # ------------------------------------------------

            if len(new_pass) < 6:

                err_lbl.configure(
                    text="Password must be at least 6 characters."
                )

                return

            # ------------------------------------------------
            # HASH
            # ------------------------------------------------

            hashed_pw = bcrypt.hashpw(
                new_pass.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            try:

                conn = sqlite3.connect(
                    DB_NAME
                )

                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO staff (
                        surname,
                        other_names,
                        position,
                        staff_id,
                        phone,
                        email,
                        password_hash,
                        locked_until
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        surname,
                        other_names,
                        position,
                        new_id,
                        phone,
                        email or None,
                        hashed_pw
                    )
                )

                new_staff_pk = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO staff_preferences (
                        staff_id,
                        notify_teacher,
                        cc_principal,
                        notify_method
                    )
                    VALUES (?, 0, 0, 'Email Only')
                    """,
                    (new_staff_pk,)
                )

                conn.commit()

                conn.close()

                # Clear fields.
                surname_entry.delete(
                    0,
                    "end"
                )

                other_names_entry.delete(
                    0,
                    "end"
                )

                id_entry.delete(
                    0,
                    "end"
                )

                phone_entry.delete(
                    0,
                    "end"
                )

                email_entry.delete(
                    0,
                    "end"
                )

                pass_entry.delete(
                    0,
                    "end"
                )

                err_lbl.configure(
                    text="Staff added successfully!",
                    text_color=SUCCESS
                )

                refresh_list()

            except sqlite3.IntegrityError:

                err_lbl.configure(
                    text=(
                        "Error: Staff ID, phone number, "
                        "or email already exists."
                    ),
                    text_color=DANGER
                )

            except Exception as exc:

                err_lbl.configure(
                    text=str(exc),
                    text_color=DANGER
                )

        ctk.CTkButton(
            form_frame,
            text="Add",
            command=add_staff,
            width=70,
            fg_color=PRIMARY
        ).grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        # ====================================================
        # STAFF LIST
        # ====================================================

        list_frame = ctk.CTkScrollableFrame(
            dlg
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(10, 20)
        )

        # ====================================================
        # DELETE STAFF
        # ====================================================

        def delete_staff(
            user_id
        ):

            conn = sqlite3.connect(
                DB_NAME
            )

            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM staff"
            )

            count = (
                cursor.fetchone()[0]
            )

            if count <= 1:

                messagebox.showerror(
                    "Error",
                    (
                        "Cannot delete the last "
                        "remaining staff account."
                    ),
                    parent=dlg
                )

                conn.close()

                return

            cursor.execute(
                """
                SELECT staff_id
                FROM staff
                WHERE id=?
                """,
                (user_id,)
            )

            row = cursor.fetchone()

            if not row:

                conn.close()

                return

            selected_staff_id = row[0]

            if (
                self.logged_in_user
                and selected_staff_id
                == self.logged_in_user.get(
                    "staff_id"
                )
            ):

                messagebox.showerror(
                    "Error",
                    "You cannot delete your own account.",
                    parent=dlg
                )

                conn.close()

                return

            if messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this account?",
                parent=dlg
            ):

                cursor.execute(
                    """
                    DELETE FROM staff
                    WHERE id=?
                    """,
                    (user_id,)
                )

                conn.commit()

            conn.close()

            refresh_list()

        # ====================================================
        # REFRESH STAFF
        # ====================================================

        def refresh_list():

            for widget in list_frame.winfo_children():

                widget.destroy()

            conn = sqlite3.connect(
                DB_NAME
            )

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    surname,
                    other_names,
                    position,
                    staff_id,
                    phone,
                    email
                FROM staff
                ORDER BY surname COLLATE NOCASE
                """
            )

            staff_members = (
                cursor.fetchall()
            )

            conn.close()

            # ------------------------------------------------
            # HEADER
            # ------------------------------------------------

            header = ctk.CTkFrame(
                list_frame,
                fg_color=SIDEBAR_BG
            )

            header.pack(
                fill="x",
                pady=(0, 5)
            )

            ctk.CTkLabel(
                header,
                text="STAFF",
                font=self.font_bold,
                width=180,
                anchor="w"
            ).pack(
                side="left",
                padx=10,
                pady=8
            )

            ctk.CTkLabel(
                header,
                text="ID",
                font=self.font_bold,
                width=130,
                anchor="w"
            ).pack(
                side="left",
                padx=10
            )

            ctk.CTkLabel(
                header,
                text="POSITION",
                font=self.font_bold,
                width=90,
                anchor="w"
            ).pack(
                side="left",
                padx=10
            )

            for row in staff_members:

                (
                    user_id,
                    surname,
                    other_names,
                    position,
                    staff_id,
                    phone,
                    email
                ) = row

                row_frame = ctk.CTkFrame(
                    list_frame
                )

                row_frame.pack(
                    fill="x",
                    pady=2
                )

                full_name = (
                    f"{other_names} {surname}"
                ).strip()

                ctk.CTkLabel(
                    row_frame,
                    text=full_name,
                    width=180,
                    anchor="w"
                ).pack(
                    side="left",
                    padx=10,
                    pady=8
                )

                ctk.CTkLabel(
                    row_frame,
                    text=staff_id,
                    width=130,
                    anchor="w"
                ).pack(
                    side="left",
                    padx=10
                )

                ctk.CTkLabel(
                    row_frame,
                    text=position,
                    width=90,
                    anchor="w"
                ).pack(
                    side="left",
                    padx=10
                )

                if not (
                    self.logged_in_user
                    and staff_id
                    == self.logged_in_user.get(
                        "staff_id"
                    )
                ):

                    ctk.CTkButton(
                        row_frame,
                        text="Delete",
                        fg_color=DANGER,
                        hover_color="#b91c1c",
                        width=60,
                        command=lambda uid=user_id:
                            delete_staff(uid)
                    ).pack(
                        side="right",
                        padx=10,
                        pady=5
                    )

        refresh_list()

    # ========================================================
    # AFTER / DESTROY
    # ========================================================

    def after(
        self,
        ms,
        func=None,
        *args
    ):

        task_id = super().after(
            ms,
            func,
            *args
        )

        if not hasattr(
            self,
            "pending_tasks"
        ):

            self.pending_tasks = []

        self.pending_tasks.append(
            task_id
        )

        return task_id

    def destroy(self):

        if hasattr(
            self,
            "pending_tasks"
        ):

            for task_id in self.pending_tasks:

                try:

                    self.after_cancel(
                        task_id
                    )

                except Exception:
                    pass

        try:

            if hasattr(
                self,
                "conn"
            ):

                self.conn.close()

        except Exception:
            pass

        super().destroy()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    ensure_database()

    login_app = LoginWindow()

    login_app.mainloop()
0