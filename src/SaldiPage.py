import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font
import json

from utilities import saldi_path

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
