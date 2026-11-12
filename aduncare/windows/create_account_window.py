import customtkinter as ctk
import bcrypt
from windows.confirmation_window import ConfirmationWindow
from utils.validation import validate_name, validate_phone, validate_email, evaluate_password_strength
from utils.id_generator import generate_unique_staff_id
from utils.db import is_phone_taken, is_email_taken, insert_staff
from utils.theme import (
    COLOR_PRIMARY_DARK,
    COLOR_BACKGROUND_LIGHT,
    COLOR_PANEL_LIGHT,
    COLOR_ERROR,
    COLOR_SUCCESS,
    COLOR_INPUT_BORDER_DEFAULT,
    get_font,
    ensure_poppins_loaded,
)


class CreateAccountWindow(ctk.CTkToplevel):
    """The setup form for capturing and validating staff registration details."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pending_tasks = []
        self.parent = parent
        self.title("Create Account Setup")
        # Increased height slightly to 650 to ensure everything fits without scrolling
        self.geometry("1000x650")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Font was already registered by MainWindow at app startup; this call
        # is idempotent/cheap and just guards against standalone use.
        ensure_poppins_loaded()

        # Flat brand-color background, matching the approved design mockup
        self.configure(fg_color=COLOR_BACKGROUND_LIGHT)

        self.staff_id_var = ctk.StringVar()
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def schedule_task(self, ms, func):
        task_id = self.after(ms, func)
        self.pending_tasks.append(task_id)
        return task_id

    def destroy(self):
        for task_id in self.pending_tasks:
            try:
                self.after_cancel(task_id)
            except:
                pass
        super().destroy()

    def _build_ui(self):
        # Header badge
        header = ctk.CTkLabel(self, text="CREATE ACCOUNT", font=get_font(size=24, weight="bold"),
                                fg_color=COLOR_PRIMARY_DARK, text_color="white", corner_radius=22,
                                width=300, height=45)
        header.place(relx=0.5, y=30, anchor="center")

        # Left Column - Independent Frame, transparent so the brand background shows through
        left_frame = ctk.CTkFrame(self, fg_color="transparent", width=400, height=550)
        left_frame.place(x=50, y=70)
        left_frame.grid_propagate(False)

        # Packed tightly with smaller pady to fit perfectly
        self.ent_surname = self._make_labeled_entry(left_frame, "SURNAME:", "YOUR LAST NAME")
        self.ent_other = self._make_labeled_entry(left_frame, "OTHER NAMES:", "FIRST AND MIDDLE NAMES")

        ctk.CTkLabel(left_frame, text="POSITION:", font=get_font(weight="bold"),
                     text_color="black").pack(anchor="w", pady=(5, 0))
        self.cbo_position = ctk.CTkComboBox(left_frame, values=["DOCTOR", "NURSE", "CORPER-DOC", "CORPER-NURSE", "INTERN"],
                                            state="readonly", width=400, height=35,
                                            fg_color=COLOR_PANEL_LIGHT, text_color="black",
                                            button_color=COLOR_PRIMARY_DARK,
                                            dropdown_fg_color=COLOR_PANEL_LIGHT,
                                            font=get_font())
        self.cbo_position.pack(pady=(0, 5))
        self.cbo_position.set("")

        id_lbl = ctk.CTkLabel(left_frame, text="ID NUMBER:", font=get_font(weight="bold"), text_color="black")
        id_lbl.pack(anchor="w", pady=(5, 0))

        id_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        id_row.pack(fill="x", pady=(0, 5))

        self.ent_id = ctk.CTkEntry(id_row, textvariable=self.staff_id_var, width=250, height=35, state="readonly",
                                    placeholder_text="XXX-XXX-XXXX", fg_color=COLOR_PANEL_LIGHT,
                                    text_color="black", font=get_font())
        self.ent_id.pack(side="left")

        self.btn_generate = ctk.CTkButton(id_row, text="GENERATE", font=get_font(weight="bold"),
                                            fg_color=COLOR_PRIMARY_DARK, text_color="white",
                                            width=130, height=35,
                                            command=self.on_generate, state="disabled")
        self.btn_generate.pack(side="right")

        self.ent_phone = self._make_labeled_entry(left_frame, "PHONE NUMBER:", "+234 XXX XXX XXXX")
        self.ent_email = self._make_labeled_entry(left_frame, "EMAIL:", "myexample@email.com")

        # Right Column - Independent Frame, transparent so the brand background shows through
        right_frame = ctk.CTkFrame(self, fg_color="transparent", width=400, height=550)
        right_frame.place(x=550, y=70)
        right_frame.grid_propagate(False)

        self.ent_pass = self._make_password_entry(right_frame, "PASSWORD:")
        self.ent_confirm = self._make_password_entry(right_frame, "CONFIRM PASSWORD:")

        self.lbl_pass_err = ctk.CTkLabel(right_frame, text="", text_color=COLOR_ERROR, font=get_font(size=12))
        self.lbl_pass_err.pack(anchor="w")

        note_text = "NOTE:\n1. YOUR PASSWORD MUST BE 8\nCHARACTERS, IT MUST HAVE A\nCAPITAL LETTER, NUMBERS AND\nSPECIAL CHARACTERS"
        ctk.CTkLabel(right_frame, text=note_text, justify="left", font=get_font(weight="bold"),
                     text_color="black").pack(anchor="w", pady=(15, 15))

        self.lbl_global_err = ctk.CTkLabel(right_frame, text="", text_color=COLOR_ERROR, font=get_font(weight="bold"))
        self.lbl_global_err.pack(anchor="se", pady=(30, 0))

        self.btn_create = ctk.CTkButton(right_frame, text="CREATE", font=get_font(size=20, weight="bold"),
                                        fg_color=COLOR_PRIMARY_DARK, hover_color="#2A3D54", text_color="white",
                                        corner_radius=25, width=150, height=50,
                                        command=self.on_create, state="disabled")
        self.btn_create.pack(anchor="se", pady=(5, 0))

        # Live validations
        self.ent_surname.bind("<KeyRelease>", self.validate_all_live)
        self.ent_other.bind("<KeyRelease>", self.validate_all_live)
        self.ent_phone.bind("<KeyRelease>", self.validate_all_live)
        self.ent_email.bind("<KeyRelease>", self.validate_all_live)
        self.ent_pass.bind("<KeyRelease>", self.validate_all_live)
        self.ent_confirm.bind("<KeyRelease>", self.validate_all_live)

    def _make_labeled_entry(self, parent, label_text, placeholder) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label_text, font=get_font(weight="bold"), text_color="black").pack(anchor="w", pady=(5, 0))
        entry = ctk.CTkEntry(parent, width=400, height=35, placeholder_text=placeholder,
                              fg_color=COLOR_PANEL_LIGHT, text_color="black", font=get_font())
        entry.pack(pady=(0, 5))
        return entry

    def _make_password_entry(self, parent, label_text) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label_text, font=get_font(weight="bold"), text_color="black").pack(anchor="w", pady=(5, 0))
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 5))

        entry = ctk.CTkEntry(frame, width=320, height=35, show="*",
                              fg_color=COLOR_PANEL_LIGHT, text_color="black", font=get_font())
        entry.pack(side="left")

        btn_show = ctk.CTkButton(frame, text="SHOW", font=get_font(size=12, weight="bold"),
                                    width=70, height=35, fg_color="white", text_color="black", hover_color="#e0e0e0",
                                    command=lambda: self._toggle_password(entry, btn_show))
        btn_show.pack(side="right")
        return entry

    def _toggle_password(self, entry: ctk.CTkEntry, btn: ctk.CTkButton):
        if entry.cget("show") == "*":
            entry.configure(show="")
            btn.configure(text="HIDE")
        else:
            entry.configure(show="*")
            btn.configure(text="SHOW")

    def validate_all_live(self, event=None):
        sur_valid = validate_name(self.ent_surname.get())
        oth_valid = validate_name(self.ent_other.get())

        if sur_valid and oth_valid:
            self.btn_generate.configure(state="normal")
        else:
            self.btn_generate.configure(state="disabled")

        pwd_valid = evaluate_password_strength(self.ent_pass.get()) != "Invalid"
        passwords_match = (self.ent_pass.get() == self.ent_confirm.get()) and (len(self.ent_pass.get()) > 0)

        if len(self.ent_confirm.get()) > 0 and not passwords_match:
            self.lbl_pass_err.configure(text="Passwords do not match!")
            self.ent_pass.configure(border_color=COLOR_ERROR)
            self.ent_confirm.configure(border_color=COLOR_ERROR)
        else:
            self.lbl_pass_err.configure(text="")
            self.ent_pass.configure(border_color=COLOR_INPUT_BORDER_DEFAULT)
            self.ent_confirm.configure(border_color=COLOR_INPUT_BORDER_DEFAULT)

        all_ready = (sur_valid and oth_valid and
                        validate_phone(self.ent_phone.get()) and
                        validate_email(self.ent_email.get()) and
                        pwd_valid and passwords_match and
                        len(self.staff_id_var.get()) > 0)

        if all_ready:
            self.btn_create.configure(state="normal")
        else:
            self.btn_create.configure(state="disabled")

    def on_generate(self):
        try:
            new_id = generate_unique_staff_id(self.ent_surname.get(), self.ent_other.get(), self.cbo_position.get())
            self.staff_id_var.set(new_id)
            self.validate_all_live()
            self.lbl_global_err.configure(text="")
        except ValueError as e:
            self.lbl_global_err.configure(text=str(e))

    def on_create(self):
        surname = self.ent_surname.get().strip()
        other = self.ent_other.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        staff_id = self.staff_id_var.get()
        password = self.ent_pass.get()
        position = self.cbo_position.get()

        if is_phone_taken(phone):
            self.lbl_global_err.configure(text="Phone number already registered.")
            return
        if email and is_email_taken(email):
            self.lbl_global_err.configure(text="Email already registered.")
            return

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            insert_staff(surname, other, position, staff_id, phone, email, hashed_pw)
            self.lbl_global_err.configure(text="Success! Preparing confirmation...", text_color=COLOR_SUCCESS)
            self.btn_create.configure(state="disabled")

            self.after(1000, lambda: self.show_confirmation(staff_id, password))
        except Exception as e:
            self.lbl_global_err.configure(text="Database Error.", text_color=COLOR_ERROR)
            print(f"DB Error: {e}")

    def show_confirmation(self, staff_id: str, plain_password: str):
        self.withdraw()
        self.conf_win = ConfirmationWindow(self, staff_id, plain_password)

    def on_cancel(self):
        self.destroy()
        self.parent.deiconify()
