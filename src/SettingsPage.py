import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from tkinter.font import Font
from tkinter import simpledialog
import json

from ReportPage import *
import SaldiPage
from utilities import usersettings_path

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
        # Save settings and determine if critical settings that affect saldi calculations have changed
        critical_settings_changed = self.save_config()  # Let's make save_config return a boolean
        
        # Only recalculate saldi if necessary
        if critical_settings_changed:
            self.controller.calculate_saldi()
            if SaldiPage in self.controller.frames:
                self.controller.frames[SaldiPage].refresh()

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
        # Load old settings to detect changes
        old_settings = self.controller.load_user_settings()

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

        # Update working hours and check for input validity
        for day, (from_entry, to_entry) in self.work_hours_entries.items():
            from_time = datetime.strptime(from_entry.get(), '%H:%M')
            to_time = datetime.strptime(to_entry.get(), '%H:%M')
            if to_time < from_time:
                messagebox.showerror("Error", "Start time cannot be before end time.")
                return False  # Return False indicating that the settings have not been successfully updated
            else:
                total_duration = to_time - from_time
                hours_in_decimal = total_duration.seconds / 3600
                total_formatted = self.controller.decimal_to_hours_minutes(hours_in_decimal)
                self.config["WorkHours"][day] = {
                    "From": from_entry.get(),
                    "To": to_entry.get(),
                    "Total": total_formatted
                }

        # Update checkbox states
        self.config["UseNormalHoursAsDefault"] = self.use_normal_hours_var.get()
        self.config["UseAvgWeekHoursAsDefault"] = self.use_avgWeekHours_var.get()

        # Save the configuration to a file
        with open(usersettings_path, "w") as file:
            json.dump(self.config, file, indent=4)

        # Calculate hours per week and day
        weekly_hours = self.controller.beregn_ugetimer()
        self.config["HoursPerWeek"] = weekly_hours
        self.config["HoursPerDay"] = weekly_hours / 5
        with open(usersettings_path, "w") as file:
            json.dump(self.config, file, indent=4)

        # Determine if recalculation is necessary by comparing critical settings
        flex_bias_changed = old_settings['Bias'].get('Flex', '') != self.config['Bias'].get('Flex', '')
        ferie_bias_changed = old_settings['Bias'].get('Ferie', '') != self.config['Bias'].get('Ferie', '')

        self.controller.calculate_and_refresh_saldi() 

        # Return True if recalculation is necessary
        return flex_bias_changed or ferie_bias_changed



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
