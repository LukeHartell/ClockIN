import tkinter as tk
from tkinter import messagebox
import csv
import os
import sys
import json
from datetime import datetime, date

from CalendarPage import CalendarPage
from SaldiPage import SaldiPage
from SettingsPage import SettingsPage
from ReportPage import ReportPage
from NewDayOffPage import NewDayOffPage

from config import get_default_settings
from utilities import timesheet_path, usersettings_path, saldi_path, projectname, version

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(f"{projectname} {version}")
        self.geometry('1000x700')
        self.resizable(False, False)

        # Set the icon path correctly depending on whether the app is frozen (packaged)
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundled executable (using PyInstaller)
            base_path = sys._MEIPASS
        else:
            # If the application is run in a development environment
            base_path = os.path.dirname(__file__)

        # icon_path = os.path.join(base_path, 'assets', 'logo.ico')
        # self.iconbitmap(icon_path)

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
        # self.calculate_saldi()

        #self.show_welcomemsg()

        ###############################################
        #       UI
        ############################################### 

    def show_welcomemsg(self):
        messagebox.showinfo("Velkommen til ClockIN", "Med ClockIN kan du holde styr på mødetider, felx, ferie og meget andet.")

    def show_frame(self, context):
        '''Raise a frame to the top for display'''
        frame = self.frames[context]
        frame.tkraise()
        # Check if the frame being shown is SaldiPage and call refresh if it is
        if context == SaldiPage:
            frame.refresh()
        if context == CalendarPage:
            frame.on_date_select(self)

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
                # # print(f"Error: Incorrect time format for {day}. Expected 'hh:mm'. Received From: {work_hours[day].get('From')} and To: {work_hours[day].get('To')}")
                hours_total = 0
                break

        return hours_total

    def setup_frames_and_menu(self):
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (CalendarPage, SaldiPage, SettingsPage, ReportPage, NewDayOffPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(CalendarPage)

        menu = tk.Menu(self)
        self.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Kalender", command=lambda: self.show_frame(CalendarPage))
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
        # print("Starting saldi calculation...")
        self.user_settings = self.load_user_settings()  # Reload settings to ensure they are up-to-date
        # print("Current settings being used:", self.user_settings)  # Show current settings

        # Now extract biases and show them
        biases = self.user_settings.get('Bias', {})
        # print("Biases fetched for calculation:", biases)

        # Proceed with extracting specific biases and calculation
        flex_bias = self.hours_minutes_to_decimal(biases.get('Flex', "0:00"))
        # print("Flex Bias after conversion:", flex_bias)

        # Calculate each type of saldo
        self.saldi['flex'] = self.calculate_flex_saldo()
        self.saldi['ferie'] = self.calculate_ferie_saldo()
        self.saldi['6. ferieuge'] = self.calculate_sjette_ferieuge_saldo()
        self.saldi['omsorgsdage'] = self.calculate_omsorgsdage_saldo()
        self.saldi['seniordage'] = self.calculate_seniordage_saldo()

        # Log calculated saldi
        # print("Calculated saldi:", self.saldi)

        # Save and refresh UI if necessary
        self.save_saldi(self.saldi)
        if SaldiPage in self.frames:
            self.frames[SaldiPage].refresh()
        # print("Saldi calculation completed and UI refreshed (if applicable).")




    def calculate_months_since(self, employment_date_str):
        employment_date = datetime.strptime(employment_date_str, "%d-%m-%Y").date()
        start_of_year = date(date.today().year, 1, 1)
        start_date = max(employment_date, start_of_year)
        current_date = date.today()
        return (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month) + 1

        ###############################################
        #       Udregn saldo af typer
        ###############################################



    def calculate_flex_saldo(self):
        initial_flex = self.load_user_saldi().get('flex', 0)  # Fallback to 0 if missing
        flex_bias_setting = self.user_settings.get('Bias', {}).get('Flex', "0:00")
        flex_bias_decimal = self.hours_minutes_to_decimal(flex_bias_setting)
        flex_consumed = self.calculate_flex_consumption()

        new_flex_saldo = initial_flex + flex_bias_decimal - flex_consumed

        print(f"Initial Flex: {initial_flex}, + Bias: {flex_bias_decimal}, - Consumed: {flex_consumed}, New Flex: {new_flex_saldo} <------------")

        return new_flex_saldo



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
            # print(f"Error processing timesheet: {e}")
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
            # print(f"Error processing timesheet: {e}")
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
            # print(f"Error processing timesheet: {e}")
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
            # print(f"Error processing timesheet: {e}")
        return total_consumption




        ###############################################
        #       Gem og indlæs
        ###############################################


    def save_saldi(self, saldi):
        try:
            with open(saldi_path, 'w') as file:
                json.dump(saldi, file, indent=4)
        except IOError as e:
            messagebox.showerror("Error", f"Error saving saldi: {e}")



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
        # Collect current settings for comparison
        old_settings = self.load_user_settings()
        
        # Collect new settings from the UI
        new_settings = self.collect_settings()
        
        # Save the new settings to user_settings.json
        with open(usersettings_path, 'w') as file:
            json.dump(new_settings, file, indent=4)
        
        # Check if the changes in settings affect saldi calculation
        if self.settings_changed(new_settings, old_settings):
            # If relevant changes are made, then recalculate saldi
            # self.calculate_saldi()
            
            # Refresh the SaldiPage if it's currently loaded
            if SaldiPage in self.frames:
                self.frames[SaldiPage].refresh()

    def settings_changed(self, new_settings, old_settings):
        # Check if work hours or biases have changed
        return (new_settings.get('WorkHours') != old_settings.get('WorkHours') or
                new_settings.get('Bias') != old_settings.get('Bias'))




    def load_user_settings(self):
        try:
            with open(usersettings_path, 'r') as file:
                settings = json.load(file)
                # print("Loaded user settings:", settings)  # Debug output
                return settings
        except FileNotFoundError:
            messagebox.showerror("Fejl", f"File not found: {usersettings_path}. Try restarting the app.")
            return self.get_default_settings()


    def load_user_saldi(self):
        """
        Load the saldi from storage. This function only loads the stored values without applying any biases.
        """
        try:
            with open(saldi_path, 'r') as file:
                saldi = json.load(file)
                # print(f"Saldi loaded successfully: {saldi}")  # Debug # print to check what's loaded
                return saldi
        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {saldi_path}. Starting with default settings.")
            return self.get_default_saldi()
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error reading the saldi file. Check file integrity.")
            return self.get_default_saldi()

        
    def get_default_saldi(self):
        return {"flex": 0, "ferie": 0, "6. ferieuge": 0, "omsorgsdage": 0, "seniordage": 0}


    def calculate_and_refresh_saldi(self):
        self.calculate_saldi()
        if 'SaldiPage' in self.frames:
            self.frames['SaldiPage'].refresh()  # Adjust this line according to your actual UI refresh method
        # Add any other UI components that need refreshing




        ###############################################
        #       Omregning mellem decimal-timer og base6 tidformat
        ###############################################

    def decimal_to_hours_minutes(self, decimal_hours):
        if decimal_hours is None:
            return "00:00"  # Return a default string if the input is None

        sign = -1 if decimal_hours < 0 else 1
        hours = int(abs(decimal_hours))
        minutes = int((abs(decimal_hours) - hours) * 60)

        if sign < 0:
            return f"-{hours:02}:{minutes:02}"
        else:
            return f"{hours:02}:{minutes:02}"



    def hours_minutes_to_decimal(self, time_str):
        try:
            hours, minutes = map(int, time_str.split(':'))
            if hours < 0:
                return hours - abs(minutes) / 60.0
            else:
                return hours + minutes / 60.0
        except ValueError:
            # print(f"Error converting time to decimal: Invalid format '{time_str}'")
            return 0

