from tkinter import messagebox
import csv
import os
from datetime import datetime
import json
from config import get_default_settings
from decimal import getcontext, Decimal

# Set the precision for Decimal operations
getcontext().prec = 6


sheet_headers = ['Dato', 'Starttid', 'Sluttid', 'Arbejdstid', 'Normtid', 'Flex saldo', 'Flex forbrug', 'Ferie forbrug', '6. Ferieuge forbrug', 'Omsorgsdage forbrug', 'Seniordage forbrug']

appdata_path = os.getenv('APPDATA')
projectname = "ClockIN"
version = "Alpha"
current_year = str(datetime.now().year)

usersettings_path = os.path.join(appdata_path, projectname, 'user_settings.json')
timesheet_path = os.path.join(appdata_path, projectname, current_year, f'timesheet_{current_year}.csv')
saldi_path = os.path.join(appdata_path, projectname, current_year, f'Saldi_{current_year}.json')

def initialize_files():
    """Initialize necessary files and directories for the application."""
    try:
        create_project_directories()
        initialize_default_files()
    except Exception as e:
        messagebox.showerror("Initialization Error", f"Failed to initialize application files: {str(e)}")

def create_project_directories():
    """Create the base and yearly directories for the application."""
    project_folder = os.path.join(appdata_path, projectname)
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)

    current_year_folder = os.path.join(project_folder, current_year)
    if not os.path.exists(current_year_folder):
        os.makedirs(current_year_folder)

def initialize_default_files():
    """Create default files with initial data if they do not exist."""
    if not os.path.exists(usersettings_path):
        with open(usersettings_path, 'w') as file:
            json.dump(get_default_settings(), file, indent=4)

    if not os.path.exists(timesheet_path):
        with open(timesheet_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=sheet_headers, delimiter=';')
            writer.writeheader()

    if not os.path.exists(saldi_path):
        with open(saldi_path, 'w') as file:
            json.dump({"ferie": 0, "flex": 0, "6. ferieuge": 0, "omsorgsdage": 0, "seniordage": 0}, file, indent=4)
