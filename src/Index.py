from MainApplication import MainApplication
from utilities import initialize_files
import sys

projectname = "ClockIN"
version = "(Alpha)"

def on_close():
        app.destroy()

if getattr(sys, 'frozen', False):
    import pyi_splash

if __name__ == "__main__":
    # Initialize necessary files and directories
    initialize_files()

    if getattr(sys, 'frozen', False):
        pyi_splash.close()

    # Start the main application
    app = MainApplication()
    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()
