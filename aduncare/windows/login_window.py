import re
import time
import hashlib
import sqlite3
import bcrypt
import os
import customtkinter as ctk

from utils.db import DB_PATH as DB_NAME
from utils.theme import (
    COLOR_PRIMARY_DARK,
    COLOR_BACKGROUND_LIGHT,
    COLOR_PANEL_LIGHT,
    COLOR_ERROR,
    get_font,
    ensure_poppins_loaded,
)

from main_app import ClinicPortalApp


class LoginWindow(ctk.CTk):
    """Staff login screen."""

    def __init__(self):
        super().__init__()

        self.title("AdunCare - Staff Login")
        self.geometry("480x620")
        self.resizable(False, False)

        ensure_poppins_loaded()

        self.configure(fg_color=COLOR_BACKGROUND_LIGHT)

        # Tracks failed attempts per ID
        self.failed_attempts = {}

        # =========================
        # CARD
        # =========================
        self.card = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL_LIGHT,
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

        # =========================
        # HEADER
        # =========================
        self.lbl_header = ctk.CTkLabel(
            self.card,
            text="LOGIN",
            font=get_font(size=30, weight="bold"),
            text_color=COLOR_PRIMARY_DARK
        )

        self.lbl_header.pack(pady=(40, 30))

        # =========================
        # ID NUMBER
        # =========================
        self.lbl_id = ctk.CTkLabel(
            self.card,
            text="ID NUMBER",
            font=get_font(size=12, weight="bold"),
            text_color="black"
        )

        self.lbl_id.pack(
            anchor="w",
            padx=40,
            pady=(10, 0)
        )

        self.id_entry = ctk.CTkEntry(
            self.card,
            height=45,
            fg_color="white",
            border_color="black",
            border_width=2,
            corner_radius=8,
            text_color="black",
            font=get_font()
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

        # =========================
        # PASSWORD
        # =========================
        self.lbl_pass = ctk.CTkLabel(
            self.card,
            text="PASSWORD",
            font=get_font(size=12, weight="bold"),
            text_color="black"
        )

        self.lbl_pass.pack(
            anchor="w",
            padx=40
        )

        self.pass_entry = ctk.CTkEntry(
            self.card,
            height=45,
            fg_color="white",
            border_color="black",
            border_width=2,
            corner_radius=8,
            show="*",
            text_color="black",
            font=get_font()
        )

        self.pass_entry.pack(
            fill="x",
            padx=40,
            pady=(5, 5)
        )

        # =========================
        # ERROR MESSAGE
        # =========================
        self.lbl_error = ctk.CTkLabel(
            self.card,
            text="",
            text_color=COLOR_ERROR,
            font=get_font(size=12, weight="bold")
        )

        self.lbl_error.pack(
            pady=(0, 15)
        )

        # =========================
        # LOGIN BUTTON
        # =========================
        self.btn_login = ctk.CTkButton(
            self.card,
            text="LOGIN",
            font=get_font(size=16, weight="bold"),
            fg_color=COLOR_PRIMARY_DARK,
            hover_color="#2A3D54",
            text_color="white",
            corner_radius=25,
            height=50,
            command=self._attempt_login
        )

        self.btn_login.pack(
            fill="x",
            padx=40,
            pady=(10, 20)
        )

        # Press Enter to login
        self.bind(
            "<Return>",
            lambda event: self._attempt_login()
        )

    # ==========================================================
    # FORMAT ID
    # ==========================================================

    def _format_id_input(self, event):

        # Ignore navigation/deletion keys
        if event.keysym in (
            "BackSpace",
            "Delete",
            "Left",
            "Right"
        ):
            return

        # Remove existing hyphens and convert to uppercase
        raw_text = (
            self.id_entry.get()
            .replace("-", "")
            .upper()
        )

        formatted = ""

        # Add hyphens after positions 3 and 6
        for i, char in enumerate(raw_text):

            if i == 3 or i == 6:
                formatted += "-"

            formatted += char

        # Maximum:
        # XXX-XXX-XXXX
        formatted = formatted[:12]

        self.id_entry.delete(0, "end")
        self.id_entry.insert(0, formatted)

    # ==========================================================
    # LOGIN
    # ==========================================================

    def _attempt_login(self):

        id_val = self.id_entry.get().strip().upper()
        pass_val = self.pass_entry.get()

        print("\n========== LOGIN DEBUG ==========")
        print("ID entered:", repr(id_val))
        print(
            "Password entered: YES"
            if pass_val
            else
            "Password entered: NO"
        )

        # ------------------------------------------------------
        # Check empty fields
        # ------------------------------------------------------

        if not id_val or not pass_val:

            print("RESULT: Missing ID or password")

            self.lbl_error.configure(
                text="Please enter ID and password."
            )

            return

        # ------------------------------------------------------
        # Check ID format
        # ------------------------------------------------------

        id_format_valid = bool(
            re.match(
                r"^[A-Z]{3}-[A-Z]{3}-\d{4}$",
                id_val
            )
        )

        print("ID format valid:", id_format_valid)

        if not id_format_valid:

            print("RESULT: Invalid ID format")

            self.lbl_error.configure(
                text="Please enter a valid ID number."
            )

            return

        # ------------------------------------------------------
        # Connect to database
        # ------------------------------------------------------

        print(
            "Database being used:",
            os.path.abspath(DB_NAME)
        )

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # ------------------------------------------------------
        # Find user
        # ------------------------------------------------------

        cursor.execute(
            "SELECT * FROM staff WHERE staff_id = ?",
            (id_val,)
        )

        user = cursor.fetchone()

        print("User found:", user is not None)

        # ------------------------------------------------------
        # User exists
        # ------------------------------------------------------

        if user:

            print(
                "Stored ID:",
                repr(user["staff_id"])
            )

            print(
                "Hash exists:",
                bool(user["password_hash"])
            )

            print(
                "Hash prefix:",
                user["password_hash"][:7]
            )

            # --------------------------------------------------
            # Check lockout
            # --------------------------------------------------

            locked_until = 0

            if "locked_until" in user.keys():
                if user["locked_until"] is not None:
                    locked_until = user["locked_until"]

            if locked_until > time.time():

                print("RESULT: ACCOUNT CURRENTLY LOCKED")

                self._start_lockout_ui(
                    locked_until,
                    id_val
                )

                conn.close()

                return

            # --------------------------------------------------
            # Check password
            # --------------------------------------------------

            try:

                is_valid = bcrypt.checkpw(
                    pass_val.encode("utf-8"),
                    user["password_hash"].encode("utf-8")
                )

                print(
                    "Bcrypt password check:",
                    is_valid
                )

            except Exception as e:

                print(
                    "BCRYPT ERROR:",
                    type(e).__name__,
                    str(e)
                )

                # Fallback for old SHA-256 accounts
                is_valid = (
                    hashlib.sha256(
                        pass_val.encode()
                    ).hexdigest()
                    == user["password_hash"]
                )

                print(
                    "SHA-256 fallback check:",
                    is_valid
                )

            # --------------------------------------------------
            # PASSWORD CORRECT
            # --------------------------------------------------

            if is_valid:

                print(
                    "RESULT: PASSWORD CORRECT"
                )

                print(
                    "Attempting to open ClinicPortalApp..."
                )

                # Reset lockout
                cursor.execute(
                    """
                    UPDATE staff
                    SET locked_until = 0
                    WHERE staff_id = ?
                    """,
                    (id_val,)
                )

                conn.commit()
                conn.close()

                # Close login window
                self.destroy()

                # Open main application
                app = ClinicPortalApp(
                    logged_in_user=dict(user)
                )

                app.mainloop()

                return

            # --------------------------------------------------
            # PASSWORD INCORRECT
            # --------------------------------------------------

            else:

                print(
                    "RESULT: PASSWORD INCORRECT"
                )

                self.failed_attempts[id_val] = (
                    self.failed_attempts.get(id_val, 0) + 1
                )

                attempts = self.failed_attempts[id_val]

                print(
                    "Failed attempts:",
                    attempts
                )

                # Lock after 4 failed attempts
                if attempts >= 4:

                    lock_time = time.time() + 60

                    cursor.execute(
                        """
                        UPDATE staff
                        SET locked_until = ?
                        WHERE staff_id = ?
                        """,
                        (lock_time, id_val)
                    )

                    conn.commit()

                    self._start_lockout_ui(
                        lock_time,
                        id_val
                    )

                    conn.close()

                    return

        # ------------------------------------------------------
        # USER DOES NOT EXIST OR PASSWORD INCORRECT
        # ------------------------------------------------------

        else:

            print(
                "RESULT: ID NOT FOUND"
            )

        self.lbl_error.configure(
            text="Invalid ID number or password."
        )

        self.pass_entry.delete(
            0,
            "end"
        )

        conn.close()

    # ==========================================================
    # LOCKOUT UI
    # ==========================================================

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

    # ==========================================================
    # LOCKOUT COUNTDOWN
    # ==========================================================

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

            # Reset database lock
            conn = sqlite3.connect(DB_NAME)

            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE staff
                SET locked_until = 0
                WHERE staff_id = ?
                """,
                (id_val,)
            )

            conn.commit()
            conn.close()