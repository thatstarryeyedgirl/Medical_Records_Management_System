import customtkinter as ctk
from PIL import Image
from windows.create_account_window import CreateAccountWindow
from utils.theme import (
    COLOR_PRIMARY_DARK,
    COLOR_BACKGROUND_LIGHT,
    get_font,
    ensure_poppins_loaded,
)


class MainWindow(ctk.CTk):
    """The permanent single root window of the application."""

    def __init__(self):
        super().__init__()
        self.title("AdunCare - System Launch")
        self.geometry("1000x600")
        self.resizable(False, False)

        self.create_account_win = None

        # Register the bundled Poppins font for this process. Must run
        # after the Tk root (self) exists, and before any get_font() call.
        ensure_poppins_loaded()

        # Flat brand-color background, matching the approved design mockup
        self.configure(fg_color=COLOR_BACKGROUND_LIGHT)

        self._build_ui()

    def _build_ui(self):
        # Use provided logo explicitly by verbatim name
        try:
            logo_img = Image.open("assets/LOGO ADUNCARE.png")
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(320, 100))
            self.logo_image = logo_ctk  # keep a reference to prevent garbage collection
            ctk.CTkLabel(self, image=logo_ctk, text="").place(relx=0.5, rely=0.25, anchor="center")
        except Exception as e:
            print(f"Warning: Could not load logo: {e}")
            ctk.CTkLabel(self, fg_color="transparent", text="ADUN Care",
                         font=get_font(size=40, weight="bold"),
                         text_color=COLOR_PRIMARY_DARK).place(relx=0.5, rely=0.25, anchor="center")

        ctk.CTkLabel(self, fg_color="transparent", text="Welcome!",
                     font=get_font(size=18, weight="bold"),
                     text_color="black").place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(self, fg_color="transparent",
                     text="New staff? Create an account to access medical records. Need help? See a supervisor.",
                     font=get_font(size=14, weight="bold"),
                     text_color="black").place(relx=0.5, rely=0.5, anchor="center")

        btn_create = ctk.CTkButton(self, text="CREATE ACCOUNT", font=get_font(size=24, weight="bold"),
                                    fg_color=COLOR_PRIMARY_DARK, hover_color="#2A3D54",
                                    text_color="white", corner_radius=30,
                                    width=350, height=60, command=self.open_create_account)
        btn_create.place(relx=0.5, rely=0.65, anchor="center")

    def open_create_account(self):
        """Hides the main window and launches the Create Account workflow."""
        if self.create_account_win is None or not self.create_account_win.winfo_exists():
            self.withdraw()  # Hide main window
            self.create_account_win = CreateAccountWindow(self)
        else:
            self.create_account_win.focus()
