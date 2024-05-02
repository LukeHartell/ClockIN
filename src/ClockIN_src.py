projectname = "ClockIN"
version = "1.9.1 (Alpha)"


import tkinter as tk
from tkinter import messagebox
import csv
import sys
import os
from datetime import datetime, date, timedelta
from tkcalendar import Calendar
from tktimepicker import AnalogPicker, constants, AnalogThemes
from tkinter.font import Font
from tkinter import ttk, simpledialog
import json
from decimal import Decimal, getcontext, InvalidOperation


# if getattr(sys, 'frozen', False):
#     import pyi_splash

# Set the precision for Decimal operations
getcontext().prec = 6

def on_close():
        app.destroy()  # This ensures the application is terminated properly

# Get the path to the %APPDATA% folder
appdata_path = os.getenv('APPDATA')

current_year = str(datetime.now().year)

usersettings_path = os.path.join(appdata_path, projectname, 'user_settings.json')
timesheet_path = os.path.join(appdata_path, projectname, current_year, f'timesheet_{current_year}.csv')
saldi_path = os.path.join(appdata_path, projectname, current_year, f'Saldi_{current_year}.json')

sheet_headers = ['Dato', 'Starttid', 'Sluttid', 'Arbejdstid', 'Normtid', 'Flex saldo', 'Flex forbrug', 'Ferie forbrug', '6. Ferieuge forbrug', 'Omsorgsdage forbrug', 'Seniordage forbrug']

def initialize_files():
    try:
        # Base folder for the project
        project_folder = os.path.join(appdata_path, projectname)
        if not os.path.exists(project_folder):
            os.makedirs(project_folder)

        # Year-specific folder for current year
        current_year_folder = os.path.join(project_folder, current_year)
        if not os.path.exists(current_year_folder):
            os.makedirs(current_year_folder)

        # Check and create user_settings.json with default settings
        if not os.path.exists(usersettings_path):
            with open(usersettings_path, 'w') as file:
                json.dump(get_default_settings(), file, indent=4)

        # Check and create timesheet.csv with headers
        if not os.path.exists(timesheet_path):
            with open(timesheet_path, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=sheet_headers, delimiter=';')
                writer.writeheader()

        # Check and create Saldi.json if it doesn't exist with default values
        if not os.path.exists(saldi_path):
            with open(saldi_path, 'w') as file:
                json.dump({"ferie": 0, "flex": 0, "6. ferieuge": 0, "omsorgsdage": 0, "seniordage": 0}, file, indent=4)

    except Exception as e:
        messagebox.showerror("Fejl", f"Failed to initialize application files: {str(e)}")
        print(f"Failed to initialize application files: {str(e)}")
        # Handle errors or raise to stop application launch if critical



# Danish day and month names
danish_months = ("Januar", "Februar", "Marts", "April", "Maj", "Juni", "Juli", "August", "September", "Oktober", "November", "December")
danish_days = ("Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn")

def get_default_settings():
    return {
        "UseNormalHoursAsDefault": False,
        "UseAvgWeekHoursAsDefault": False,
        "WorkHours": {
            "Mandag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Tirsdag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Onsdag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Torsdag": {"From": "08:00", "To": "15:45", "Total": "7:45"},
            "Fredag": {"From": "08:00", "To": "14:00", "Total": "6:00"}
        },
        "Children": [],
        "UserDetails": {
            "EmploymentDate": "31-12-1999",
            "BirthDate": "31-12-1999"
        },
        "HoursPerWeek": 37.0,
        "HoursPerDay": 7.4,
        "Bias": {
            "Flex": "0:00",
            "Ferie": "0:00",
            "Six_ferie": "0:00",
            "Careday": "0",
            "Seniorday": "0"
        }
    }

"""

 █████  ██████  ██████  
██   ██ ██   ██ ██   ██ 
███████ ██████  ██████  
██   ██ ██      ██      
██   ██ ██      ██      

"""
class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(f"{projectname} - {version}")
        self.geometry('1000x700')
        self.iconbitmap("assets/logo.ico")
        self.resizable(False, False)

        # Ensure the directories exist, and if not, create them
        for file_path in [timesheet_path, usersettings_path, saldi_path]:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write default settings if the user settings file does not exist
        self.ensure_default_settings()

        # Load settings
        self.user_settings = self.load_user_settings()
        self.user_saldi = self.load_user_saldi()

        # Initialize saldi dictionary
        self.saldi = {}

        # Setup of the application frames and menu first
        self.frames = {}
        self.setup_frames_and_menu()

        # Calculate all saldi after the frames are setup
        self.calculate_saldi()

        #self.show_welcomemsg()

    def setup_frames_and_menu(self):
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (MainPage, SaldiPage, SettingsPage, ReportPage, NewDayOff):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainPage)

        menu = tk.Menu(self)
        self.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Kalender", command=lambda: self.show_frame(MainPage))
        menu.add_cascade(label="Saldi", command=lambda: self.show_frame(SaldiPage))
        menu.add_cascade(label="Rapporter", command=lambda: self.show_frame(ReportPage))
        menu.add_cascade(label="Indstillinger", command=lambda: self.show_frame(SettingsPage))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

    def ensure_default_settings(self):
        if not os.path.exists(usersettings_path):
            self.write_default_settings_if_needed(usersettings_path, get_default_settings())

    def write_default_settings_if_needed(self, settings_path, default_settings):
        with open(settings_path, 'w') as file:
            json.dump(default_settings, file, indent=4)


        ###############################################
        #       Beregning af saldi
        ############################################### 


    def calculate_saldi(self):
        """
        Calculate all saldi, applying biases correctly and ensuring no duplication in bias application.
        This method is called whenever changes require saldi recalculation.
        """
        current_saldi = self.load_user_saldi()  # Load current saldi without bias applied
        biases = self.user_settings.get('Bias', {})

        # Apply biases correctly
        flex_bias = biases.get('Flex', "0:00")
        flex_bias = self.hours_minutes_to_decimal(flex_bias)

        self.saldi['flex'] = current_saldi['flex'] + float(flex_bias) - self.calculate_flex_consumption()
        self.saldi['ferie'] = self.calculate_ferie_saldo()
        self.saldi['6. ferieuge'] = self.calculate_sjette_ferieuge_saldo()
        self.saldi['omsorgsdage'] = self.calculate_omsorgsdage_saldo()
        self.saldi['seniordage'] = self.calculate_seniordage_saldo()

        self.save_saldi(self.saldi)
        if SaldiPage in self.frames:
            self.frames[SaldiPage].refresh()

    def calculate_months_since(self, employment_date_str):
        employment_date = datetime.strptime(employment_date_str, "%d-%m-%Y").date()
        start_of_year = date(date.today().year, 1, 1)
        start_date = max(employment_date, start_of_year)
        current_date = date.today()
        return (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month) + 1



        ###############################################
        #       Udregn forbrug af typer
        ###############################################



    def calculate_flex_consumption(self):
        current_year = datetime.now().year
        total_consumption = 0
        try:
            with open(timesheet_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    if datetime.strptime(row['Dato'], "%d-%m-%Y").year == current_year:
                        if (row.get('Flex forbrug')):
                            total_consumption += float(row.get('Flex forbrug', 0))
        except Exception as e:
            messagebox.showerror("Fejl", f"Error processing timesheet: {e}")
            print(f"Error processing timesheet: {e}")
        return total_consumption

    def calculate_ferie_consumption(self):
        current_year = datetime.now().year
        total_consumption = 0
        try:
            with open(timesheet_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    if datetime.strptime(row['Dato'], "%d-%m-%Y").year == current_year:
                        if (row.get('Ferie forbrug')):
                            total_consumption += float(row.get('Ferie forbrug', 0))
        except Exception as e:
            messagebox.showerror("Fejl", f"Error processing timesheet: {e}")
            print(f"Error processing timesheet: {e}")
        return total_consumption

    def calculate_careday_consumption(self):
        current_year = datetime.now().year
        total_consumption = 0
        try:
            with open(timesheet_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    if datetime.strptime(row['Dato'], "%d-%m-%Y").year == current_year:
                        if (row.get('Omsorgsdage forbrug')):
                            total_consumption += float(row.get('Omsorgsdage forbrug', 0))
        except Exception as e:
            messagebox.showerror("Fejl", f"Error processing timesheet: {e}")
            print(f"Error processing timesheet: {e}")
        return total_consumption
    
    def calculate_seniorday_consumption(self):
        current_year = datetime.now().year
        total_consumption = 0
        try:
            with open(timesheet_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    if datetime.strptime(row['Dato'], "%d-%m-%Y").year == current_year:
                        if (row.get('Seniordage forbrug')):
                            total_consumption += float(row.get('Seniordage forbrug', 0))
        except Exception as e:
            messagebox.showerror("Fejl", f"Error processing timesheet: {e}")
            print(f"Error processing timesheet: {e}")
        return total_consumption


        ###############################################
        #       Udregn saldo af typer
        ###############################################



    def calculate_flex_saldo(self):
        # udregning af flex

        """
        Specifically handle flex saldo calculation, ensuring no repeated bias application.
        """
        initial_flex = self.load_user_saldi().get('flex', 0)  # Load the initial flex saldo
        flex_bias = float(self.user_settings.get('Bias', {}).get('Flex', 0))
        flex_bias = self.controller.hours_minutes_to_decimal(flex_bias)

        flex_consumed = self.calculate_flex_consumption()

        return initial_flex + flex_bias - flex_consumed  # Apply bias only once

        # if (self.user_saldi.get('flex')):
        #     T = float(self.user_saldi.get('flex'))
        # else:
        #     T = 0

        # if (self.user_settings.get('Bias', {}).get('Flex')):
        #     O = float(self.user_settings.get('Bias', {}).get('Flex'))
        # else:
        #     O = 0
        # F = self.calculate_flex_consumption()
        
        # # Tjent + Opsparet - Forbrug
        # return T + O - F

    def calculate_ferie_saldo(self):
        employment_date_str = self.user_settings.get('UserDetails', {}).get('EmploymentDate')
        M = self.calculate_months_since(employment_date_str)            # 
        T:float = 15.42                                                 # Man opsparer 15,42 timers ferie hver måned
        if (self.user_settings.get('Bias', {}).get('Ferie')):           # Overført ferie kan oplyses i indstillinger
            O = self.user_settings.get('Bias', {}).get('Ferie')
            O = float(self.hours_minutes_to_decimal(O))
        else:
            O = 0   
        F = self.calculate_ferie_consumption()                          # Udregner hvor meget ferie, der er registreret i timesheet.csv
        
        # Ferie saldo = (T)akst * antal (M)åneder + (O)verføre timer - (F)erietimer brugt
        
        return (M * T) + O - F

    def calculate_sjette_ferieuge_saldo(self):
        # udregning af 6. ferieuge
        return 0

    def calculate_omsorgsdage_saldo(self):
        # Get the current year
        current_year = datetime.now().year
        
        # Retrieve the list of children from the JSON data
        children = self.user_settings.get('Children', [])
        
        # Calculate how many children are under the age of 8
        children_under_eight = 0
        for child in children:
            year_of_birth = int(child['YearOfBirth'])
            age = current_year - year_of_birth
            
            # Check if the child is under 8 years old and does not turn 8 this year
            if age < 8:
                children_under_eight += 1

        if (self.user_settings.get('Bias', {}).get('Careday')):
            O = float(self.user_settings.get('Bias', {}).get('Careday'))
        else:
            O = 0   
        F = self.calculate_careday_consumption()

        # Return the count of children under 8 multiplied by 2
        return (children_under_eight * 2) + O - F

    def calculate_seniordage_saldo(self):
        # Get the current date
        T = 0
        today = datetime.now()
        current_year = today.year
        end_of_year = datetime(current_year, 12, 31)

        # Retrieve the user's birthdate from the JSON data
        birth_date_str = self.user_settings.get('UserDetails', {}).get('BirthDate', '')
        
        # Parse the birthdate string into a datetime object
        try:
            birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y")
        except ValueError:
            return 0  # Return 0 if the birthdate is not properly formatted or missing
        
        # Calculate the age of the user at the end of this year
        age_at_end_of_year = end_of_year.year - birth_date.year
        
        # Adjust for the user's birthday not yet occurring this year
        if (birth_date.month, birth_date.day) > (end_of_year.month, end_of_year.day):
            age_at_end_of_year -= 1

        # Check if the user is or will be 60 or older by the end of this year
        if age_at_end_of_year >= 60:
            T = 2
        

        if (self.user_settings.get('Bias', {}).get('Seniorday')):
            O = float(self.user_settings.get('Bias', {}).get('Seniorday'))
        else:
            O = 0   
        F = self.calculate_seniorday_consumption()

        return T + O - F


        ###############################################
        #       Gem og indlæs
        ###############################################


    def save_saldi(self, saldi):
        try:
            with open(saldi_path, 'w') as file:
                json.dump(saldi, file, indent=4)
        except IOError as e:
            messagebox.showerror("Fejl", f"Error saving saldi: {e}")
            print(f"Error saving saldi: {e}")

    def collect_settings(self):
        # Collect data from entries and return as a dictionary
        return {
            "UserDetails": {
                "EmploymentDate": self.employdate_entry.get(),
                "Name": self.name_entry.get(),
                "Department": self.department_entry.get(),
                "Email": self.email_entry.get(),
            },
            "WorkHours": {day: (entry[0].get(), entry[1].get()) for day, entry in self.work_hours_entries.items()},
            "UseNormalHoursAsDefault": self.use_normal_hours_var.get(),
            "UseAvgWeekHoursAsDefault": self.use_avgWeekHours_var.get(),
        }

    def save_settings(self):
        # Logic to save settings...
        self.controller.save_user_settings(self.collect_settings())
        self.controller.calculate_saldi()  # Recalculate saldi after settings update
        self.controller.frames[SaldiPage].refresh()  # Ensure the SaldiPage is updated

    def load_user_settings(self):
        # Indlæser og retunerer alle data i user_settings.json. Hvis filen ikke findes meldes en fejl og programmet benytter i midlertid default-settings.
        # Denne metode benyttes af mange andre funktioner i programmet.
        try:
            with open(usersettings_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Fejl", f"File  not found: {usersettings_path}. Try restarting the app.")
            return self.get_default_settings()

    def load_user_saldi(self):
        """
        Load the saldi from storage. This function only loads the stored values without applying any biases.
        """
        try:
            with open(saldi_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", "File not found: {saldi_path}. Starting with default settings.")
            return self.get_default_saldi()
        
    def get_default_saldi(self):
        """
        Provides a default saldi dictionary, typically used when no saldi file exists.
        """
        return {"flex": 0, "ferie": 0, "6. ferieuge": 0, "omsorgsdage": 0, "seniordage": 0}



        ###############################################
        #       UI
        ############################################### 

    def show_welcomemsg(self):
        messagebox.showinfo("Velkommen til ClockIN", "Med ClockIN kan du holde styr på mødetider, felx, ferie og meget andet.")

    def show_frame(self, context):
        '''Raise a frame to the top for display'''
        frame = self.frames[context]
        frame.tkraise()

    def beregn_ugetimer(self):
        loaded_settings = self.load_user_settings()
        work_hours = loaded_settings['WorkHours']
        hours_total = 0

        for day in work_hours:
            try:
                # Parse the 'From' and 'To' times
                time_format = "%H:%M"
                from_time = datetime.strptime(work_hours[day]['From'], time_format)
                to_time = datetime.strptime(work_hours[day]['To'], time_format)

                # Calculate the duration in hours
                duration = (to_time - from_time).seconds / 3600
                hours_total += duration
            except ValueError:
                messagebox.showerror("Fejl", f"Forkert format for {day}. Tider skal skrives i samme format som følgende eksempeler: 12:00 eller 08:30")
                # print(f"Error: Incorrect time format for {day}. Expected 'hh:mm'. Received From: {work_hours[day].get('From')} and To: {work_hours[day].get('To')}")
                hours_total = 0
                break

        return hours_total
    



        ###############################################
        #       Omregning mellem decimal-timer og base6 tidformat
        ###############################################

    def decimal_to_hours_minutes(self, decimal_hours):
        """Convert decimal hours to a formatted string of hours and minutes."""
        # Extract the sign for the hours and apply it uniformly to hours and minutes
        sign = -1 if decimal_hours < 0 else 1

        # Calculate absolute values for hours and minutes
        hours = int(abs(decimal_hours))
        minutes = int((abs(decimal_hours) - hours) * 60)

        # Format string based on original sign
        if sign < 0:
            return f"-{hours:02}:{minutes:02}"
        else:
            return f"{hours:02}:{minutes:02}"
    

    def hours_minutes_to_decimal(self, time_str):
        """Convert a string formatted as 'HH:MM' to decimal hours, correctly handling negative times."""
        hours, minutes = map(int, time_str.split(':'))
        if hours < 0:
            # When hours are negative, we subtract the minutes converted to hours to keep the time negative.
            return hours - abs(minutes) / 60.0
        else:
            # When hours are positive, we add the minutes converted to hours.
            return hours + minutes / 60.0








"""

██   ██  █████  ██      ███████ ███    ██ ██████  ███████ ██████                               
██  ██  ██   ██ ██      ██      ████   ██ ██   ██ ██      ██   ██                              
█████   ███████ ██      █████   ██ ██  ██ ██   ██ █████   ██████                               
██  ██  ██   ██ ██      ██      ██  ██ ██ ██   ██ ██      ██   ██                              
██   ██ ██   ██ ███████ ███████ ██   ████ ██████  ███████ ██   ██

"""
class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_widgets()
        self.load_flexhours_to_widget()

    def setup_widgets(self):
        self.times_data = self.read_all_data()
        cal_font = Font(size=12)

        # Main horizontal layout frame
        frame_main_horizontal = tk.Frame(self)
        frame_main_horizontal.pack(side="top", fill="both", expand=True)

        # Calendar frame
        frame_calendar = tk.Frame(frame_main_horizontal)
        frame_calendar.pack(side="left", fill="both", padx=(50, 0), expand=True)

        # Calendar widget
        self.calendar = Calendar(frame_calendar, selectmode='day', font=cal_font, locale='da_DK', daynames=danish_days, monthnames=danish_months, selectbackground='#00695e', selectforeground='white')
        self.calendar.pack(pady=20, fill="both", expand=True)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

        # Frame for new buttons to the right of the calendar
        frame_buttons = tk.Frame(frame_main_horizontal)
        frame_buttons.pack(side="right", fill="both", padx=25)

        # Flex labels with saldo
        self.label_flex_total = tk.Label(frame_buttons, text="Flex i alt: 999", font=Font(size=16, weight="bold"))
        self.label_flex_total.pack(side="top", padx=20, pady=(50, 10))

        self.label_flex_week = tk.Label(frame_buttons, text="Flex i denne uge: 999", font=Font(size=12))
        self.label_flex_week.pack(side="top", padx=20)

        # Button to register new off day
        btn_new1 = tk.Button(frame_buttons, text="Registrér fri", font=Font(size=12, weight="bold"), padx=40, pady=20, background="#f59725", foreground="White", command=lambda: self.controller.show_frame(NewDayOff))
        btn_new1.pack(side="bottom", padx=20, pady=20)

        # Time pickers and labels in a single frame using grid layout
        frame_time_pickers = tk.Frame(self)
        frame_time_pickers.pack(padx=(50, 45), pady=20, fill="both", expand=True)

        # Clock in picker, label, and current time button
        label_clock_in = tk.Label(frame_time_pickers, text="Indtjekningstid", font=Font(size=14))
        label_clock_in.grid(row=0, column=0, padx=(0, 20))
        self.clock_in_picker = AnalogPicker(frame_time_pickers, type=constants.HOURS24)
        self.clock_in_picker.grid(row=1, column=0, padx=(0, 20))
        btn_current_time_in = tk.Button(frame_time_pickers, text="Tjek ind nu", font=Font(size=12), command=lambda: self.set_current_time(self.clock_in_picker))
        btn_current_time_in.grid(row=2, column=0, padx=(0, 20))

        # Save and Clear buttons
        btn_save = tk.Button(frame_time_pickers, text="Gem", font=Font(size=16, weight="bold"), padx=10, pady=70, command=self.save_times, background='#009687', foreground='white')
        btn_save.grid(row=1, column=1, padx=10)
        btn_clear = tk.Button(frame_time_pickers, text="Ryd", font=Font(size=12), padx=5, pady=0, command=self.clear_times, background='#f44336', foreground='white')
        btn_clear.grid(row=2, column=1, padx=0)

        # Clock out picker, label, and current time button
        label_clock_out = tk.Label(frame_time_pickers, text="Udtjekningstid", font=Font(size=14))
        label_clock_out.grid(row=0, column=2, padx=(20, 0))
        self.clock_out_picker = AnalogPicker(frame_time_pickers, type=constants.HOURS24)
        self.clock_out_picker.grid(row=1, column=2, padx=(20, 0))
        btn_current_time_out = tk.Button(frame_time_pickers, text="Tjek ud nu", font=Font(size=12), command=lambda: self.set_current_time(self.clock_out_picker))
        btn_current_time_out.grid(row=2, column=2, padx=(20, 0))

        # Apply themes to the time pickers
        theme_in = AnalogThemes(self.clock_in_picker)
        theme_in.setNavyBlue()
        theme_out = AnalogThemes(self.clock_out_picker)
        theme_out.setNavyBlue()

        self.refresh_calendar()  # Initial refresh to mark the calendar
        self.on_date_select(None)  # Set initial values for pickers

    def on_date_select(self, event):
        # Called when a date is clicked in the calendar
        settings = self.controller.load_user_settings()
        date, selected_day = self.get_date_and_day()

        self.update_time_entries(date, settings, selected_day)

    def get_date_and_day(self):
        date = self.calendar.selection_get().strftime("%d-%m-%Y")
        day_of_week = datetime.strptime(date, "%d-%m-%Y").weekday()
        days = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
        selected_day = days[day_of_week] if day_of_week < len(days) else None
        return date, selected_day

    def update_time_entries(self, date, settings, selected_day):
        default_time = "00:00"
        if date in self.times_data:
            clock_in, clock_out = self.times_data[date]['Starttid'], self.times_data[date]['Sluttid']
        elif settings["UseNormalHoursAsDefault"] and selected_day in settings["WorkHours"]:
            clock_in = settings["WorkHours"][selected_day].get("From", default_time)
            clock_out = settings["WorkHours"][selected_day].get("To", default_time)
        else:
            clock_in, clock_out = default_time, default_time

        self.set_time_pickers(clock_in, clock_out)

    def set_time_pickers(self, clock_in, clock_out):
        clock_in_hour, clock_in_minute = self.validate_and_parse_time(clock_in)
        clock_out_hour, clock_out_minute = self.validate_and_parse_time(clock_out)

        self.clock_in_picker.setHours(clock_in_hour)
        self.clock_in_picker.setMinutes(clock_in_minute)
        self.clock_out_picker.setHours(clock_out_hour)
        self.clock_out_picker.setMinutes(clock_out_minute)

        self.load_flexhours_to_widget()

    def validate_and_parse_time(self, time_str):
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour, minute
        except ValueError:
            return 0, 0  # Default to 0:00 if the time is not valid

    def read_all_data(self):
        data = {}
        try:
            with open(timesheet_path, mode='r', newline='') as file:
                reader = csv.DictReader(file, delimiter=';')
                for row in reader:
                    data[row['Dato']] = {
                        'Starttid': row['Starttid'],
                        'Sluttid': row['Sluttid'],
                        'Normtid': row['Normtid']
                    }
        except FileNotFoundError:
            messagebox.showerror("Fejl", f"File not found at {timesheet_path}")
            exit()
        except Exception as e:
            messagebox.showerror("Fejl", f"Error reading file: {str(e)}")
            exit()
        return data






    def load_balances(self):
        """ Load or initialize balances from a JSON file. """
        try:
            with open(saldi_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {'flex': 0}  # Return default if no file exists

    def save_balances(self, balances):
        try:
            with open(saldi_path, 'w') as file:
                json.dump(balances, file, indent=4)
        except Exception as e:
            print(f"Failed to save balances: {e}")



    def write_all_data(self, data):
        user_settings = self.controller.load_user_settings()
        use_avg_hours = user_settings.get('UseAvgWeekHoursAsDefault', False)

        current_normtid_decimal = self.get_normtid_decimal(user_settings)

        flex_saldo = Decimal('0')
        balances = self.load_balances()

        with open(timesheet_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=sheet_headers, delimiter=';')
            writer.writeheader()

            for key, value in data.items():
                date, selected_day = self.get_date_and_day_from_key(key)
                normtid_at_entry = self.get_daily_norm(selected_day, use_avg_hours, user_settings, current_normtid_decimal)

                start_time = datetime.strptime(value['Starttid'], '%H:%M')
                end_time = datetime.strptime(value['Sluttid'], '%H:%M')
                duration = end_time - start_time
                arbejdstid_minutes = duration.seconds // 60

                daily_flex_minutes = arbejdstid_minutes - (normtid_at_entry * 60)
                daily_flex_hours = Decimal(daily_flex_minutes) / Decimal('60.0')
                flex_saldo += daily_flex_hours

                writer.writerow({
                    'Dato': key,
                    'Starttid': value['Starttid'],
                    'Sluttid': value['Sluttid'],
                    'Arbejdstid': f"{arbejdstid_minutes // 60:02}:{arbejdstid_minutes % 60:02}",
                    'Normtid': self.controller.decimal_to_hours_minutes(normtid_at_entry),
                    'Flex saldo': self.controller.decimal_to_hours_minutes(flex_saldo),
                    'Flex forbrug': '',
                    'Ferie forbrug': '',
                    '6. Ferieuge forbrug': '',
                    'Omsorgsdage forbrug': '',
                    'Seniordage forbrug': ''
                })

        self.update_balances_and_refresh(flex_saldo, user_settings, balances)

    def calculate_weekly_flex(self):
        today = datetime.today()
        monday = today - timedelta(days=today.weekday())  # Monday of this week
        sunday = monday + timedelta(days=6)  # Sunday of this week

        weekly_flex = Decimal('0')
        balances = self.load_balances()
        timesheet = self.read_all_data()  # This reads a JSON or similar format where each day's data is stored

        for key, value in timesheet.items():
            date = datetime.strptime(key, "%d-%m-%Y")
            if monday <= date <= sunday:  # Now includes days until Sunday
                start_time = datetime.strptime(value['Starttid'], '%H:%M')
                end_time = datetime.strptime(value['Sluttid'], '%H:%M')
                duration = end_time - start_time
                arbejdstid_minutes = duration.seconds // 60
                normtid = self.controller.hours_minutes_to_decimal(value['Normtid'])
                daily_flex_minutes = arbejdstid_minutes - (normtid * 60)
                weekly_flex += Decimal(daily_flex_minutes) / Decimal('60.0')

        balances['flex_week'] = float(weekly_flex)
        self.save_balances(balances)
        return weekly_flex


    def get_normtid_decimal(self, user_settings):
        # Handles the parsing of 'HoursPerDay'
        normtid_str = str(user_settings.get('HoursPerDay', '7.40'))
        try:
            return Decimal(normtid_str) if ":" not in normtid_str else self.controller.hours_minutes_to_decimal(normtid_str)
        except InvalidOperation:
            return Decimal('7.40')  # Fallback

    def get_daily_norm(self, selected_day, use_avg_hours, user_settings, current_normtid_decimal):
        if use_avg_hours:
            return current_normtid_decimal
        else:
            work_hours = user_settings.get('WorkHours', {})
            day_hours_str = work_hours.get(selected_day, {}).get('Total', None)
            if day_hours_str:
                return self.controller.hours_minutes_to_decimal(day_hours_str)
            else:
                return current_normtid_decimal  # Fallback if no specific hours are found

    def update_balances_and_refresh(self, flex_saldo, user_settings, balances):
        flex_bias_str = user_settings.get('Bias', {}).get('Flex', '0')
        flex_bias = Decimal(self.controller.hours_minutes_to_decimal(flex_bias_str)) if ":" in flex_bias_str else Decimal(flex_bias_str)
        final_flex_saldo = flex_saldo + flex_bias

        balances['flex'] = float(final_flex_saldo)
        self.save_balances(balances)
        self.load_flexhours_to_widget()

    def get_date_and_day_from_key(self, key):
        date = datetime.strptime(key, "%d-%m-%Y")
        day_of_week = date.weekday()
        days = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
        selected_day = days[day_of_week] if day_of_week < len(days) else None
        return date.strftime("%d-%m-%Y"), selected_day

    def refresh_calendar(self):
        self.load_flexhours_to_widget()

        self.calendar.calevent_remove('all')
        for date_str, times in self.times_data.items():
            try:
                day, month, year = map(int, date_str.split('-'))
                event_date = datetime(year, month, day)
                clock_in, clock_out = times['Starttid'], times['Sluttid']

                # Convert clock_in and clock_out to datetime objects for comparison
                time_format = "%H:%M"
                clock_in_dt = datetime.strptime(clock_in, time_format)
                clock_out_dt = datetime.strptime(clock_out, time_format)

                # Determine the appropriate tag based on the time values
                if clock_in == "00:00" or clock_out == "00:00":
                    tag = 'incomplete'
                elif clock_out_dt < clock_in_dt:
                    tag = 'error'  # Tag as 'error' if clock_out is before clock_in
                else:
                    tag = 'reported'

                self.calendar.calevent_create(event_date, 'Event', tag)
                # Apply color coding based on tags
                self.calendar.tag_config('reported', background='#009687', foreground='white')
                self.calendar.tag_config('incomplete', background='#FFD700', foreground='black')
                self.calendar.tag_config('error', background='#f44336', foreground='white')  # Red for errors
            except ValueError:
                continue  # Skip entries with invalid data


    def format_time(self, time_tuple):
        return "{:02}:{:02}".format(time_tuple[0], time_tuple[1])

    def save_times(self):
        # Called when 'save' is clicked in the calendar.
        date, selected_day = self.get_date_and_day()
        clock_in_time = self.format_time(self.clock_in_picker.time())
        clock_out_time = self.format_time(self.clock_out_picker.time())

        all_data = self.read_all_data()
        all_data[date] = {'Starttid': clock_in_time, 'Sluttid': clock_out_time}
        
        self.reset_flex_saldo()  # Reset flex saldo to initial state
        self.write_all_data(all_data)  # Recalculate new flex saldo

        self.times_data = all_data  # Reload data to reflect changes
        self.refresh_calendar()  # Refresh UI components

    def clear_times(self):
        # Get the current selected date and day from the calendar
        date, selected_day = self.get_date_and_day()
        settings = self.controller.load_user_settings()

        # Remove the date's data if it exists and update data storage
        if date in self.times_data:
            del self.times_data[date]
            self.write_all_data(self.times_data)  # Recalculate after clearing the data
            self.refresh_calendar()

        # Set the clock pickers to default or specific times based on settings
        self.set_default_times(selected_day, settings)

        # Update the flex hours display widget to show the new total after changes
        self.load_flexhours_to_widget()

    def set_default_times(self, selected_day, settings):
        default_time = "00:00"
        if settings["UseNormalHoursAsDefault"] and selected_day and selected_day in settings["WorkHours"]:
            clock_in = settings["WorkHours"][selected_day].get("From", default_time)
            clock_out = settings["WorkHours"][selected_day].get("To", default_time)
        else:
            clock_in, clock_out = default_time, default_time

        # Parse times and set clock pickers
        clock_in_hour, clock_in_minute = map(int, clock_in.split(':'))
        clock_out_hour, clock_out_minute = map(int, clock_out.split(':'))
        self.clock_in_picker.setHours(clock_in_hour)
        self.clock_in_picker.setMinutes(clock_in_minute)
        self.clock_out_picker.setHours(clock_out_hour)
        self.clock_out_picker.setMinutes(clock_out_minute)



    def set_current_time(self, picker):
        current_time = datetime.now().strftime("%H:%M").split(':')
        picker.setHours(int(current_time[0]))
        picker.setMinutes(int(current_time[1]))

        self.save_times()
        self.refresh_calendar()

    def reset_flex_saldo(self):
        # This method should set the flex saldo to zero or to a predetermined base value
        # Assuming we're loading the balance fresh each time from a 'saldi_path'
        try:
            with open(saldi_path, 'r+') as file:
                balances = json.load(file)
                balances['flex'] = 0  # Reset to zero or base value for daily calculations
                file.seek(0)
                file.truncate()
                json.dump(balances, file)
        except FileNotFoundError:
            print("Balance file not found, creating new.")
            with open(saldi_path, 'w') as file:
                json.dump({'flex': 0}, file)  # Create with base value if not found

    def load_flexhours_to_widget(self):
        self.config = self.controller.load_user_saldi()

        flex_total = self.config.get("flex", 'Fejl')
        if flex_total != 'Fejl':
            flex_total = self.controller.decimal_to_hours_minutes(flex_total)
        self.label_flex_total.config(text=f"Flex i alt: {flex_total}")

        flex_week = self.calculate_weekly_flex()  # Calculate or fetch the weekly flex time
        flex_week_formatted = self.controller.decimal_to_hours_minutes(flex_week)  # Convert to readable format
        self.label_flex_week.config(text=f"Flex i denne uge: {flex_week_formatted}")





"""

███████  █████  ██      ██████  ██                                                             
██      ██   ██ ██      ██   ██ ██                                                             
███████ ███████ ██      ██   ██ ██                                                             
     ██ ██   ██ ██      ██   ██ ██                                                             
███████ ██   ██ ███████ ██████  ██ 

"""

class SaldiPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Saldi Oversigt", font=('Helvetica', 16, 'bold')).pack(pady=(10, 5))

        # Initialize labels for each type of saldo
        self.saldi_labels = {}
        for saldo_type in ['flex', 'ferie', '6. ferieuge', 'omsorgsdage', 'seniordage']:
            if saldo_type in ['omsorgsdage', 'seniordage']:
                self.saldi_labels[saldo_type] = tk.Label(self, text=f"{saldo_type.capitalize()}: 0 dage", font=('Helvetica', 14))
                self.saldi_labels[saldo_type].pack(pady=(5, 3))
            else:
                self.saldi_labels[saldo_type] = tk.Label(self, text=f"{saldo_type.capitalize()}: 0 timer", font=('Helvetica', 14))
                self.saldi_labels[saldo_type].pack(pady=(5, 3))

        tk.Button(self, text="Opdatér", font=Font(weight="bold"), padx=20, command=self.load_and_display_saldi, background='#009687', foreground='white').pack(pady=(10, 5))

        self.load_and_display_saldi()
        # self.refresh()

    def load_and_display_saldi(self):
        """Load saldi from JSON and display it on labels."""
        self.controller.calculate_saldi()
        try:
            with open(saldi_path, 'r') as file:
                saldi_data = json.load(file)
                for saldo_type, label in self.saldi_labels.items():
                    saldo = saldi_data.get(saldo_type, "0:00")
                    if saldo_type in ["omsorgsdage", "seniordage"]:
                        label.config(text=f"{saldo_type.capitalize()}: {saldo} dage")
                    else:
                        saldo = self.controller.decimal_to_hours_minutes(saldo)
                        label.config(text=f"{saldo_type.capitalize()}: {saldo}")
        except FileNotFoundError:
            messagebox.showerror("Fejl", "Failed to load saldi data. Saldi file not found.")
            print("Failed to load saldi data. Saldi file not found.")
            exit()
        except json.JSONDecodeError:
            messagebox.showerror("Fejl", "Failed to decode saldi data. JSON format error.")
            print("Failed to decode saldi data. JSON format error.")
            exit()

    def refresh(self):
        """Load the saldo from saldi.json and update the display."""
        try:
            with open(saldi_path, 'r') as file:
                saldi = json.load(file)
            for saldo_type, label in self.saldi_labels.items():
                # Update each label with the corresponding saldo from the file
                saldo = saldi.get(saldo_type, 0)  # Get 0 if the type doesn't exist in the file
                label.config(text=f"{saldo_type.capitalize()}: {saldo} timer")
        except FileNotFoundError:
            messagebox.showerror("Fejl", "Saldi file not found.")
            print("Saldi file not found.")
            exit()
        except json.JSONDecodeError:
            messagebox.showerror("Fejl", "Error decoding JSON from saldi file.")
            print("Error decoding JSON from saldi file.")
            exit()






class ReportPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Eksportér rapport", font=('Helvetica', 16, 'bold')).pack(pady=(10, 5))


"""

███    ██ ███████ ██     ██ ██████   █████  ██    ██  ██████  ███████ ███████ 
████   ██ ██      ██     ██ ██   ██ ██   ██  ██  ██  ██    ██ ██      ██      
██ ██  ██ █████   ██  █  ██ ██   ██ ███████   ████   ██    ██ █████   █████   
██  ██ ██ ██      ██ ███ ██ ██   ██ ██   ██    ██    ██    ██ ██      ██      
██   ████ ███████  ███ ███  ██████  ██   ██    ██     ██████  ██      ██      

"""
class NewDayOff(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.config = {}
        self.config = self.controller.load_user_settings()
        #self.load_config()  # Load configuration from file

        # Setup UI elements
        tk.Label(self, text="Register New Day Off").pack(pady=(10, 0))

        # Date entry
        tk.Label(self, text="Date:").pack()
        self.date_entry = tk.Entry(self)
        self.date_entry.pack()

        # Reason entry
        tk.Label(self, text="Reason for Day Off:").pack()
        self.reason_entry = tk.Entry(self)
        self.reason_entry.pack()

        # Submit button
        submit_btn = tk.Button(self, text="Submit", command=self.register_day_off)
        submit_btn.pack(pady=10)

    def register_day_off(self):
        date = self.date_entry.get()
        reason = self.reason_entry.get()
        if not date or not reason:
            messagebox.showerror("Fejl", "Udfyld alle felter.")
            return

        # Here you might save the day off data to a file or database
        # Example: Append to a JSON file
        self.save_day_off_data(date, reason)
        messagebox.showinfo("Success", "Day off registered successfully.")
        self.date_entry.delete(0, tk.END)
        self.reason_entry.delete(0, tk.END)

    def save_day_off_data(self, date, reason):
        # Example: append new data to a JSON file (adjust as needed based on your data handling)
        try:
            with open('DaysOff.json', 'r+') as file:
                data = json.load(file)
                data.append({'date': date, 'reason': reason})
                file.seek(0)
                json.dump(data, file, indent=4)
        except FileNotFoundError:
            exit()
            #with open('DaysOff.json', 'w') as file:
            #    json.dump([{'date': date, 'reason': reason}], file, indent=4)



"""

██ ███    ██ ██████  ███████ ████████ ██ ██      ██      ██ ███    ██  ██████  ███████ ██████  
██ ████   ██ ██   ██ ██         ██    ██ ██      ██      ██ ████   ██ ██       ██      ██   ██ 
██ ██ ██  ██ ██   ██ ███████    ██    ██ ██      ██      ██ ██ ██  ██ ██   ███ █████   ██████  
██ ██  ██ ██ ██   ██      ██    ██    ██ ██      ██      ██ ██  ██ ██ ██    ██ ██      ██   ██ 
██ ██   ████ ██████  ███████    ██    ██ ███████ ███████ ██ ██   ████  ██████  ███████ ██   ██ 

"""
class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.config = {}
        self.config = self.controller.load_user_settings() # Load configuration from file
        self.load_widgets()
        self.load_settings_to_widgets()
        self.load_workhours_to_widget()
        
    def load_widgets(self):
        # User details section
        tk.Label(self, text="Oplysninger:", font=Font(weight="bold"), background="#009687", foreground="White").grid(row=0, column=0, sticky="w", padx=25, pady=7)
        tk.Label(self, text="Navn").grid(row=1, column=0, sticky="w", padx=25)
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=1, column=1, sticky="ew", columnspan=2)
        
        tk.Label(self, text="Afdeling").grid(row=2, column=0, sticky="w", padx=25)
        self.department_entry = tk.Entry(self)
        self.department_entry.grid(row=2, column=1, sticky="ew", columnspan=2)
        
        tk.Label(self, text="Mail").grid(row=3, column=0, sticky="w", padx=25)
        self.email_entry = tk.Entry(self)
        self.email_entry.grid(row=3, column=1, sticky="ew", columnspan=2)
        
        tk.Label(self, text="Ansættelsesdato").grid(row=4, column=0, sticky="w", padx=25)
        self.employdate_entry = tk.Entry(self)
        self.employdate_entry.grid(row=4, column=1, sticky="ew", columnspan=2)

        tk.Label(self, text="Fødselsdagto").grid(row=5, column=0, sticky="w", padx=25)
        self.birthdate_entry = tk.Entry(self)
        self.birthdate_entry.grid(row=5, column=1, sticky="ew", columnspan=2)

        # Opsparet
        tk.Label(self, text="Justering/Overført:", font=Font(weight="bold"), background="#009687", foreground="White").grid(row=0, column=10, sticky="w", padx=25, pady=7, columnspan=2)
        tk.Label(self, text="Flex").grid(row=1, column=10, sticky="w", padx=25)
        self.bias_flex = tk.Entry(self)
        self.bias_flex.grid(row=1, column=11, sticky="ew")
        tk.Label(self, text="timer").grid(row=1, column=12, sticky="w")
        
        tk.Label(self, text="Ferie").grid(row=2, column=10, sticky="w", padx=25)
        self.bias_ferie = tk.Entry(self)
        self.bias_ferie.grid(row=2, column=11, sticky="ew")
        tk.Label(self, text="timer").grid(row=2, column=12, sticky="w")
        
        tk.Label(self, text="6. Ferieuge").grid(row=3, column=10, sticky="w", padx=25)
        self.bias_six_ferie = tk.Entry(self)
        self.bias_six_ferie.grid(row=3, column=11, sticky="ew")
        tk.Label(self, text="timer").grid(row=3, column=12, sticky="w")
        
        tk.Label(self, text="Omsorgsdage").grid(row=4, column=10, sticky="w", padx=25)
        self.bias_careday = tk.Entry(self)
        self.bias_careday.grid(row=4, column=11, sticky="ew")
        tk.Label(self, text="dage").grid(row=4, column=12, sticky="w")

        tk.Label(self, text="Seniordage").grid(row=5, column=10, sticky="w", padx=25)
        self.bias_seniorday = tk.Entry(self)
        self.bias_seniorday.grid(row=5, column=11, sticky="ew")
        tk.Label(self, text="dage").grid(row=5, column=12, sticky="w")


        # Normal working hours
        tk.Label(self, text="Normaltider:", font=Font(weight="bold"), background="#009687", foreground="White").grid(row=6, column=0, sticky="w", padx=25, pady=7)
        self.work_hours_entries = {}
        days = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
        for i, day in enumerate(days):
            tk.Label(self, text=f"{day}").grid(row=7+i, column=0, sticky="w", padx=25)
            from_entry = tk.Entry(self)
            from_entry.grid(row=7+i, column=1, sticky="ew")
            to_entry = tk.Entry(self)
            to_entry.grid(row=7+i, column=2, sticky="ew")
            self.work_hours_entries[day] = (from_entry, to_entry)
        self.use_normal_hours_var = tk.BooleanVar()
        self.use_normal_hours_var.set(False)  # Default value
        self.use_avgWeekHours_var = tk.BooleanVar()
        self.use_avgWeekHours_var.set(False)  # Default value

        self.hours_label = tk.Label(self, text="Svarende til 37 timer/uge", font=Font(weight="bold"))
        self.hours_label.grid(row=14, column=1, columnspan=2, sticky="w", padx=25)

        use_normal_hours_checkbox = tk.Checkbutton(self, text="Brug normaltider som standard i kalenderen", variable=self.use_normal_hours_var, onvalue=True, offvalue=False)
        use_normal_hours_checkbox.grid(row=19, column=1, sticky="w", columnspan=2)

        use_avgWeekHours_checkbox = tk.Checkbutton(self, text="Brug gennemsnit til beregning af flex", variable=self.use_avgWeekHours_var, onvalue=True, offvalue=False)
        use_avgWeekHours_checkbox.grid(row=20, column=1, sticky="w", columnspan=2)

        
        # Children section
        tk.Label(self, text="Børn:", font=Font(weight="bold"), background="#009687", foreground="White").grid(row=21, column=0, sticky="w", padx=25, pady=7)
        tk.Label(self, text="(Denne information bruges til beregning af omsorgsdage)").grid(row=22, column=0, sticky="w", padx=25, columnspan=4)
        self.children_listbox = tk.Listbox(self)
        self.children_listbox.grid(row=23, column=0, columnspan=3, sticky="ew", padx=25)
        tk.Button(self, text="Tilføj barn", padx=60, command=self.add_child).grid(row=24, column=0, padx=25)
        tk.Button(self, text="Fjern valgte", padx=65, command=self.remove_selected_child).grid(row=24, column=1, columnspan=2)
        
        # Save Button with updated command to recalculate saldi
        tk.Button(self, text="Gem indstillinger", font=Font(weight="bold"), padx=20, command=self.save_and_recalculate_saldi, background='#009687', foreground='white').grid(row=25, column=0, padx=25, pady=50)

    def save_and_recalculate_saldi(self):
        self.save_config()
        self.controller.calculate_saldi()
        # self.controller.update_ui()  # Ensure this is called to refresh UI immediately
        self.load_workhours_to_widget()



    def add_child(self):
        name = "Barn"
        year = simpledialog.askstring("Tilføj barn", "Indtast fødselsår:", parent=self)
        if name and year:
            self.children_listbox.insert(tk.END, f"{name} ({year})")
            self.config["Children"].append({"Name": name, "YearOfBirth": year})

    def remove_selected_child(self):
        selected_indices = list(self.children_listbox.curselection())
        selected_indices.reverse()  # Delete from last to first to avoid index shifting
        for index in selected_indices:
            del self.config["Children"][index]
            self.children_listbox.delete(index)

    def save_config(self):
        # Capture old values to detect changes
        old_flex_bias = self.config.get('Bias', {}).get('Flex', "0:00")
        # old_flex_bias = self.controller.hours_minutes_to_decimal(old_flex_bias)

        old_ferie_bias = self.config.get('Bias', {}).get('Ferie', '0')
        # old_ferie_bias = self.controller.hours_minutes_to_decimal(old_ferie_bias)

        # Update the settings from UI components
        self.config["UserDetails"] = {
            "Name": self.name_entry.get(),
            "Department": self.department_entry.get(),
            "Email": self.email_entry.get(),
            "EmploymentDate": self.employdate_entry.get(),
            "BirthDate": self.birthdate_entry.get()
        }
        self.config["Bias"] = {
            "Flex": self.bias_flex.get(),
            "Ferie": self.bias_ferie.get(),
            "Six_ferie": self.bias_six_ferie.get(),
            "Careday": self.bias_careday.get(),
            "Seniorday": self.bias_seniorday.get()
        }




        # Update working hours
        # Iterate through each day and its associated from/to time entries
        for day, (from_entry, to_entry) in self.work_hours_entries.items():
            # Parse the "From" and "To" time string to a datetime object
            from_time = datetime.strptime(from_entry.get(), '%H:%M')
            to_time = datetime.strptime(to_entry.get(), '%H:%M')
            
            # Check if the "To" time is before the "From" time, indicating the work crossed into the next day
            if to_time < from_time:
                # Display an error message if the "To" time is earlier than the "From" time
                messagebox.showerror("Error", "Start time cannot be before end time.")
            else:
                # Calculate the time difference between "To" and "From"
                total_duration = to_time - from_time
                # Convert total duration to total hours in decimal
                hours_in_decimal = total_duration.seconds / 3600

                # Convert decimal hours to a formatted string "X hours Y minutes"
                total_formatted = self.controller.decimal_to_hours_minutes(hours_in_decimal)

                # Save the formatted duration along with the original "From" and "To" times in the configuration dictionary
                self.config["WorkHours"][day] = {
                    "From": from_entry.get(),
                    "To": to_entry.get(),
                    "Total": total_formatted
                }

        # Save the checkbox state
        self.config["UseNormalHoursAsDefault"] = self.use_normal_hours_var.get()
        self.config["UseAvgWeekHoursAsDefault"] = self.use_avgWeekHours_var.get()
        

        # Save the configuration to a file
        with open(usersettings_path, "w") as file:
            json.dump(self.config, file, indent=4)


        # Beregn timer per uge
        timer_per_uge = self.controller.beregn_ugetimer()
        self.config["HoursPerWeek"] = timer_per_uge
        self.config["HoursPerDay"] = timer_per_uge/5

        with open(usersettings_path, "w") as file:
            json.dump(self.config, file, indent=4)



        # Check if critical settings have changed
        flex_bias_changed = old_flex_bias != self.bias_flex.get()
        ferie_bias_changed = old_ferie_bias != self.bias_ferie.get()

        # Trigger recalculation if necessary
        if flex_bias_changed or ferie_bias_changed:
            self.controller.calculate_saldi()  # Recalculate all saldi

            # If this causes updates to saldi that should reflect in the UI, ensure UI is updated
            if SaldiPage in self.controller.frames:
                self.controller.frames[SaldiPage].refresh()

        # Show confirmation message
        # tk.messagebox.showinfo("Gemt", "Indstillinger gemt succesfuldt!")



    def load_settings_to_widgets(self):
        if "UserDetails" in self.config:
            self.name_entry.insert(0, self.config["UserDetails"].get("Name", ""))
            self.department_entry.insert(0, self.config["UserDetails"].get("Department", ""))
            self.email_entry.insert(0, self.config["UserDetails"].get("Email", ""))
            self.employdate_entry.insert(0, self.config["UserDetails"].get("EmploymentDate", ""))
            self.birthdate_entry.insert(0, self.config["UserDetails"].get("BirthDate", ""))

        if "Bias" in self.config:
            self.bias_flex.insert(0, self.config["Bias"].get("Flex", ""))
            self.bias_ferie.insert(0, self.config["Bias"].get("Ferie", ""))
            self.bias_six_ferie.insert(0, self.config["Bias"].get("Six_ferie", ""))
            self.bias_careday.insert(0, self.config["Bias"].get("Careday", ""))
            self.bias_seniorday.insert(0, self.config["Bias"].get("Seniorday", ""))
        
        if "WorkHours" in self.config:
            for day, (from_entry, to_entry) in self.work_hours_entries.items():
                from_entry.insert(0, self.config["WorkHours"].get(day, {}).get("From", ""))
                to_entry.insert(0, self.config["WorkHours"].get(day, {}).get("To", ""))
        
        # Set the checkbox according to the saved value
        self.use_normal_hours_var.set(self.config.get("UseNormalHoursAsDefault", False))
        self.use_avgWeekHours_var.set(self.config.get("UseAvgWeekHoursAsDefault", False))
        
        if "Children" in self.config:
            for child in self.config["Children"]:
                self.children_listbox.insert(tk.END, f"{child['Name']} ({child['YearOfBirth']})")

    def load_workhours_to_widget(self):
        week_hours = self.config.get("HoursPerWeek", 'Fejl')
        self.hours_label.config(text=f"Svarende til {week_hours} timer/uge")


if __name__ == "__main__":
    initialize_files()
    app = MainApplication()

    # if getattr(sys, 'frozen', False):
    #     pyi_splash.close()

    # Set the protocol for the window close button ('X')
    app.protocol("WM_DELETE_WINDOW", on_close)

    app.mainloop()