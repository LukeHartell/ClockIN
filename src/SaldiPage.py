import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font
import json

from utilities import saldi_path

class SaldiPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # UI setup
        tk.Label(self, text="Saldi Oversigt", font=('Helvetica', 16, 'bold')).pack(pady=(10, 5))
        self.saldi_labels = {}
        for saldo_type in ['flex', 'ferie', '6. ferieuge', 'omsorgsdage', 'seniordage']:
            unit = 'dage' if saldo_type in ['omsorgsdage', 'seniordage'] else 'timer'
            self.saldi_labels[saldo_type] = tk.Label(self, text=f"{saldo_type.capitalize()}: 0 {unit}", font=('Helvetica', 14))
            self.saldi_labels[saldo_type].pack(pady=(5, 3))

        # Button to manually refresh data
        # tk.Button(self, text="Opdatér", font=Font(weight="bold"), padx=20, command=self.refresh, background='#009687', foreground='white').pack(pady=(10, 5))

        # Initial data load
        self.controller.calculate_saldi()
        self.refresh()  # Make sure this is called after calculate_saldi()



    def load_and_display_saldi(self):
        """Load saldi from JSON and display it on labels."""
        self.controller.calculate_saldi()  # Calculate saldi
        try:
            with open(saldi_path, 'r') as file:
                saldi_data = json.load(file)
                for saldo_type, label in self.saldi_labels.items():
                    saldo = saldi_data.get(saldo_type, "0:00" if saldo_type in ["omsorgsdage", "seniordage"] else "0")
                    if saldo_type in ["omsorgsdage", "seniordage"]:
                        label.config(text=f"{saldo_type.capitalize()}: {saldo} dage")
                    else:
                        # Apply the conversion to all types except 'omsorgsdage' and 'seniordage'
                        saldo = self.controller.decimal_to_hours_minutes(saldo)
                        label.config(text=f"{saldo_type.capitalize()}: {saldo}")
        except FileNotFoundError as e:
            messagebox.showerror("Fejl", f"Failed to load saldi data: {str(e)}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Fejl", f"Failed to decode saldi data: {str(e)}")




    # def load_and_display_saldi(self):
    #     """Load saldi from JSON and display it on labels."""
    #     self.controller.calculate_saldi()
    #     try:
    #         with open(saldi_path, 'r') as file:
    #             saldi_data = json.load(file)
    #             for saldo_type, label in self.saldi_labels.items():
    #                 saldo = saldi_data.get(saldo_type, "0:00")
    #                 if saldo_type in ["omsorgsdage", "seniordage"]:
    #                     label.config(text=f"{saldo_type.capitalize()}: {saldo} dage")
    #                 else:
    #                     saldo = self.controller.decimal_to_hours_minutes(saldo)
    #                     label.config(text=f"{saldo_type.capitalize()}: {saldo}")
    #     except FileNotFoundError:
    #         messagebox.showerror("Fejl", "Failed to load saldi data. Saldi file not found.")
    #         print("Failed to load saldi data. Saldi file not found.")
    #         exit()
    #     except json.JSONDecodeError:
    #         messagebox.showerror("Fejl", "Failed to decode saldi data. JSON format error.")
    #         print("Failed to decode saldi data. JSON format error.")
    #         exit()

    def refresh(self):
        """Load the saldo from saldi.json and update the display."""
        try:
            with open(saldi_path, 'r') as file:
                saldi = json.load(file)
            for saldo_type, label in self.saldi_labels.items():
                saldo = saldi.get(saldo_type, "0:00" if saldo_type in ["omsorgsdage", "seniordage"] else "0")
                if saldo_type in ["omsorgsdage", "seniordage"]:
                    label.config(text=f"{saldo_type.capitalize()}: {saldo} dage")
                else:
                    saldo = self.controller.decimal_to_hours_minutes(saldo)
                    label.config(text=f"{saldo_type.capitalize()}: {saldo}")
        except FileNotFoundError as e:
            messagebox.showerror("Fejl", f"Saldi file not found: {str(e)}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Fejl", f"Error decoding JSON from saldi file: {str(e)}")

