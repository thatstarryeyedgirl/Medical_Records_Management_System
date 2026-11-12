import customtkinter as ctk
from utils.theme import (
    COLOR_PRIMARY_DARK,
    COLOR_BACKGROUND_LIGHT,
    COLOR_PANEL_LIGHT,
    COLOR_GOLD_ACCENT,
    COLOR_ERROR,
    get_font,
    ensure_poppins_loaded,
)


class ConfirmationWindow(ctk.CTkToplevel):
    """Window showing generated ID and plaintext password on successful creation."""

    def __init__(self, parent, staff_id: str, password: str):
        super().__init__(parent)
        self.parent = parent

        self.title("Account Created")
        self.geometry("550x670")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # Block interactions with parent

        # Font was already registered by MainWindow at app startup; this call
        # is idempotent/cheap and just guards against standalone use.
        ensure_poppins_loaded()

        # Flat brand-color background, matching the approved design mockup
        self.configure(fg_color=COLOR_BACKGROUND_LIGHT)

        self._build_ui(staff_id, password)

        # Bind close actions
        self.bind("<Return>", lambda e: self.on_close())

        # Handle the native OS window 'X' close button to follow proper flow
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self, staff_id: str, password: str):
        # Card container
        card = ctk.CTkFrame(self, fg_color=COLOR_PANEL_LIGHT, corner_radius=20, width=450, height=500)
        card.place(relx=0.5, rely=0.45, anchor="center")
        card.grid_propagate(False)

        ctk.CTkLabel(card, text="Your Account has\nbeen created \U0001F389",
                        font=get_font(size=32, weight="bold"), text_color=COLOR_GOLD_ACCENT).pack(pady=(40, 20))

        ctk.CTkLabel(card, text="ID NUMBER", font=get_font(size=14, weight="bold"), text_color="black").pack(pady=(20, 0))
        ctk.CTkLabel(card, text=staff_id, font=get_font(size=40, weight="bold"), text_color=COLOR_PRIMARY_DARK).pack(pady=(0, 20))

        ctk.CTkLabel(card, text="PASSWORD", font=get_font(size=14, weight="bold"), text_color="black").pack(pady=(20, 0))
        ctk.CTkLabel(card, text=password, font=get_font(size=40, weight="bold"), text_color=COLOR_PRIMARY_DARK).pack(pady=(0, 40))

        ctk.CTkLabel(card, text="Make sure to keep this information safe",
                        font=get_font(size=14, weight="bold"), text_color=COLOR_ERROR).pack(pady=(10, 20))

        # Close button below the card
        btn_close = ctk.CTkButton(self, text="CLOSE", font=get_font(size=24, weight="bold"),
                                    fg_color=COLOR_PRIMARY_DARK, hover_color="#2A3D54", text_color="white",
                                    corner_radius=30, height=60, width=200,
                                    command=self.on_close)
        btn_close.place(relx=0.5, rely=0.9, anchor="center")

    def on_close(self):
        """Destroys self, destroys parent (Create Setup), and restores Main Window."""
        main_window = self.parent.parent
        self.destroy()
        self.parent.destroy()
        main_window.deiconify()  # Restore the hidden main window
