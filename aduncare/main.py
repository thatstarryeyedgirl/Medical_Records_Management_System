from utils.db import init_db
from windows.main_window import MainWindow

if __name__ == "__main__":
    init_db()
    app = MainWindow()
    app.mainloop()
    