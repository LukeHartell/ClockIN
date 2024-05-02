prjectname = "ClockIN"
version = "1.0 (Beta)"


import tkinter as tk
from tkinter import messagebox, font
import csv
import sys
import os
from datetime import datetime
from tkcalendar import Calendar
from tktimepicker import AnalogPicker, constants, AnalogThemes
from tkinter.font import Font  # Import the Font class

if getattr(sys, 'frozen', False):
    import pyi_splash

def on_close():
        root.destroy()  # This ensures the application is terminated properly

# Get the path to the %APPDATA% folder
appdata_path = os.getenv('APPDATA')

# Define the path to your timesheet file within the %APPDATA% directory
timesheet_path = os.path.join(appdata_path, 'ClockIN', 'timesheet.csv')

# Ensure the directory exists, and if not, create it
os.makedirs(os.path.dirname(timesheet_path), exist_ok=True)

# Danish day and month names
danish_months = ("Januar", "Februar", "Marts", "April", "Maj", "Juni", 
                 "Juli", "August", "September", "Oktober", "November", "December")
danish_days = ("Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn")

def read_data():
    """ Read the data from the CSV into a dictionary using ';' as a delimiter. """
    data = {}
    try:
        with open(timesheet_path, mode='r', newline='') as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                if len(row) == 3:
                    data[row[0]] = row[1], row[2]
    except FileNotFoundError:
        pass  # It's okay if the file does not exist yet.
    return data

def write_data(data):
    """ Write the dictionary back to the CSV using ';' as a delimiter. """
    with open(timesheet_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        for key, value in data.items():
            writer.writerow([key, value[0], value[1]])

def refresh_calendar():
    """ Refresh the calendar by marking dates with reported times differently if incomplete. """
    # Clear all calendar events to remove old marks
    calendar.calevent_remove('all')
    # Apply new marks only to dates with data
    for date, times in times_data.items():
        year, month, day = map(int, date.split('-'))
        clock_in, clock_out = times
        # Determine the type of marking based on the time values
        if clock_in == "00:00" or clock_out == "00:00":
            # Only one timestamp reported, mark as needing completion
            tag = 'incomplete'
            calendar.calevent_create(datetime(year, month, day), 'Incomplete', tag)
        else:
            # Both timestamps reported, mark as complete
            tag = 'reported'
            calendar.calevent_create(datetime(year, month, day), 'Reported', tag)
    
    # Configure tags with colors
    calendar.tag_config('reported', background='#009687', foreground='white')
    calendar.tag_config('incomplete', background='#FFD700', foreground='black')  # Using a gold color for incomplete


def format_time(time_tuple):
    return "{:02}:{:02}".format(time_tuple[0], time_tuple[1])

def on_date_select(event):
    date = calendar.selection_get().strftime("%Y-%m-%d")
    root.update()  # Force update of the GUI before setting time
    if date in times_data:
        clock_in, clock_out = times_data[date]
        clock_in_hour, clock_in_minute = map(int, clock_in.split(':'))
        clock_out_hour, clock_out_minute = map(int, clock_out.split(':'))
        clock_in_picker.setHours(clock_in_hour)
        clock_in_picker.setMinutes(clock_in_minute)
        clock_out_picker.setHours(clock_out_hour)
        clock_out_picker.setMinutes(clock_out_minute)
    else:
        clock_in_picker.setHours(0)
        clock_in_picker.setMinutes(0)
        clock_out_picker.setHours(0)
        clock_out_picker.setMinutes(0)
    root.update()  # Force update of the GUI after setting time

def save_times():
    date = calendar.selection_get().strftime("%Y-%m-%d")
    clock_in_time = format_time(clock_in_picker.time())
    clock_out_time = format_time(clock_out_picker.time())
    times_data[date] = (clock_in_time, clock_out_time)
    write_data(times_data)
    refresh_calendar()  # Update the calendar marks after saving

def clear_times():
    date = calendar.selection_get().strftime("%Y-%m-%d")
    if date in times_data:
        # Remove the entry for the selected date
        del times_data[date]
        # Write the updated data back to the CSV
        write_data(times_data)
        # Refresh the calendar to update the display
        refresh_calendar()
        # Reset the time pickers to default values
        clock_in_picker.setHours(0)
        clock_in_picker.setMinutes(0)
        clock_out_picker.setHours(0)
        clock_out_picker.setMinutes(0)

def set_current_time(picker):
    current_time = datetime.now().strftime("%H:%M").split(':')
    picker.setHours(int(current_time[0]))
    picker.setMinutes(int(current_time[1]))

# Main window setup
root = tk.Tk()
root.title(f"{prjectname} - {version}")
root.geometry('1000x700')
root.resizable(False, False)

# Load data from CSV
times_data = read_data()

# Customize font for the calendar
cal_font = Font(size=12)

# Adjusting visible rows and columns, and setting the selected date color
calendar = Calendar(root, selectmode='day', font=cal_font, height=7, width=4,
                    locale='da_DK', day_names=danish_days, month_names=danish_months,
                    selectbackground='#00695e',  # Background color of the selected date
                    selectforeground='white')  # Text color of the selected date
calendar.pack(pady=20, padx=200, fill="both", expand=True)
calendar.bind("<<CalendarSelected>>", on_date_select)

# Time pickers and labels in a single frame using grid layout
frame_time_pickers = tk.Frame(root)
frame_time_pickers.pack(padx= 50, pady=20, fill="both", expand=True)

# Clock in picker, label and current time button
label_clock_in = tk.Label(frame_time_pickers, text="Indtjekningstid", font=Font(size=14))
label_clock_in.grid(row=0, column=0, padx=(0, 20))
clock_in_picker = AnalogPicker(frame_time_pickers, type=constants.HOURS24)
clock_in_picker.grid(row=1, column=0, padx=(0, 20))
btn_current_time_in = tk.Button(frame_time_pickers, text="Nuværende Tid", font=Font(size=12), command=lambda: set_current_time(clock_in_picker))
btn_current_time_in.grid(row=2, column=0, padx=(0, 20))

# Save and Clear buttons
btn_save = tk.Button(frame_time_pickers, text="Gem", font=Font(size=16, weight="bold"), padx=15, pady=70, command=save_times, background='#009687', foreground='white')
btn_save.grid(row=1, column=1, padx=0)
btn_clear = tk.Button(frame_time_pickers, text="Ryd", font=Font(size=12), padx=5, pady=0, command=clear_times, background='#f44336', foreground='white')
btn_clear.grid(row=2, column=1, padx=0)

# Clock out picker, label and current time button
label_clock_out = tk.Label(frame_time_pickers, text="Udtjekningstid", font=Font(size=14))
label_clock_out.grid(row=0, column=2, padx=(20, 0))
clock_out_picker = AnalogPicker(frame_time_pickers, type=constants.HOURS24)
clock_out_picker.grid(row=1, column=2, padx=(20, 0))
btn_current_time_out = tk.Button(frame_time_pickers, text="Nuværende Tid", font=Font(size=12), command=lambda: set_current_time(clock_out_picker))
btn_current_time_out.grid(row=2, column=2, padx=(20, 0))

# Apply themes to the time pickers
theme_in = AnalogThemes(clock_in_picker)
theme_in.setNavyBlue()
theme_out = AnalogThemes(clock_out_picker)
theme_out.setNavyBlue()

refresh_calendar()  # Initial refresh to mark the calendar
on_date_select(event=None)  # Set initial values for pickers


if getattr(sys, 'frozen', False):
    pyi_splash.close()

# Set the protocol for the window close button ('X')
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()