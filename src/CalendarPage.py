import tkinter as tk
from tkinter import messagebox
import csv
from datetime import datetime, timedelta
from tkcalendar import Calendar
from tktimepicker import AnalogPicker, constants, AnalogThemes
from tkinter.font import Font
import json
from decimal import Decimal, InvalidOperation

from config import *
from NewDayOffPage import *
from utilities import timesheet_path, saldi_path, sheet_headers

class CalendarPage(tk.Frame):
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
        btn_new1 = tk.Button(frame_buttons, text="Registrér fri", font=Font(size=12, weight="bold"), padx=40, pady=20, background="#f59725", foreground="White", command=lambda: self.controller.show_frame(NewDayOffPage))
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
                date_object = datetime.strptime(key, "%d-%m-%Y")

                # Initialize variables outside the conditional scope for use in writing to CSV
                normtid_at_entry = Decimal('0')
                arbejdstid_minutes = 0

                if date_object.weekday() < 5:  # Process if the day is a weekday
                    normtid_at_entry = self.get_daily_norm(selected_day, use_avg_hours, user_settings, current_normtid_decimal)
                    start_time = datetime.strptime(value['Starttid'], '%H:%M')
                    end_time = datetime.strptime(value['Sluttid'], '%H:%M')
                    duration = end_time - start_time
                    arbejdstid_minutes = duration.seconds // 60
                    daily_flex_minutes = arbejdstid_minutes - (normtid_at_entry * 60)
                    daily_flex_hours = Decimal(daily_flex_minutes) / Decimal('60.0')
                    flex_saldo += daily_flex_hours
                else:
                    start_time = datetime.strptime(value['Starttid'], '%H:%M')
                    end_time = datetime.strptime(value['Sluttid'], '%H:%M')
                    duration = end_time - start_time
                    arbejdstid_minutes = duration.seconds // 60

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

    def get_date_and_day_from_key(self, key):
        date = datetime.strptime(key, "%d-%m-%Y")
        day_of_week = date.weekday()
        days = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
        selected_day = days[day_of_week] if day_of_week < len(days) else None
        return date.strftime("%d-%m-%Y"), selected_day

    def calculate_weekly_flex(self):
        today = datetime.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        weekly_flex = Decimal('0')
        balances = self.load_balances()
        timesheet = self.read_all_data()

        for key, value in timesheet.items():
            date = datetime.strptime(key, "%d-%m-%Y")
            if monday <= date <= sunday:
                if date.weekday() < 5:  # Checks if it's a weekday (Monday=0, Sunday=6)
                    start_time = datetime.strptime(value['Starttid'], '%H:%M')
                    end_time = datetime.strptime(value['Sluttid'], '%H:%M')
                    duration = end_time - start_time
                    arbejdstid_minutes = duration.seconds // 60
                    normtid = self.controller.hours_minutes_to_decimal(value['Normtid'])
                    daily_flex_minutes = arbejdstid_minutes - (normtid * 60)
                    weekly_flex += Decimal(daily_flex_minutes) / Decimal('60.0')
                else:
                    # Handle weekend work, possibly as overtime or ignore for flex
                    # Example: Add to a separate overtime tally if needed
                    continue

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
        date, selected_day = self.get_date_and_day()  # Assuming this returns the selected date in "%d-%m-%Y" format and the day name
        date_object = datetime.strptime(date, "%d-%m-%Y")  # Convert the date string back to a datetime object for weekday checking

        # Check if the saved time is on a weekend
        if date_object.weekday() >= 5:  # 5 for Saturday, 6 for Sunday
            messagebox.showinfo("Weekend", "Du har indberettet arbejdstid i en weekend. Dette bliver gemt men tagets ikke med i beregninger af fx. flex.")

        # Process the time entries
        clock_in_time = self.format_time(self.clock_in_picker.time())
        clock_out_time = self.format_time(self.clock_out_picker.time())

        # Read existing data, update with new entry, and save
        all_data = self.read_all_data()
        all_data[date] = {'Starttid': clock_in_time, 'Sluttid': clock_out_time}
        
        self.reset_flex_saldo()  # Reset flex saldo to initial state before recalculating
        self.write_all_data(all_data)  # Write data to file and recalculate flex saldo

        self.times_data = all_data  # Reload data to reflect changes
        self.refresh_calendar()  # Refresh UI components to show updated data
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
            # print("Balance file not found, creating new.")
            with open(saldi_path, 'w') as file:
                json.dump({'flex': 0}, file)  # Create with base value if not found

    def load_flexhours_to_widget(self):
        self.config = self.controller.load_user_saldi()

        flex_total = self.config.get("flex", 0)  # Fallback to 0 if None
        # print(f"flex_total loaded: {flex_total}")

        if flex_total is None:
            flex_total = 0  # Ensure flex_total is never None

        flex_total = self.controller.decimal_to_hours_minutes(flex_total)
        self.label_flex_total.config(text=f"Flex i alt: {flex_total}")

        flex_week = self.calculate_weekly_flex()  # Assume this also returns a valid number
        flex_week_formatted = self.controller.decimal_to_hours_minutes(flex_week)
        self.label_flex_week.config(text=f"Flex i denne uge: {flex_week_formatted}")


