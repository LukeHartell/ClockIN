import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.font import Font
import json

from utilities import saldi_path

class SaldiPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Saldi Oversigt", font=('Helvetica', 32, 'bold')).pack(pady=(50, 25), fill='x', anchor='n')

        self.table_frame = tk.Frame(self)
        self.table_frame.pack(pady=(5, 10), padx=(100, 100), fill='x', anchor='n')

        # Button for manuel update. Disabled as the page updates on laod.
        # tk.Button(self, text="Opdatér", font=Font(weight="bold"), padx=20, command=self.refresh, background='#009687', foreground='white').pack(pady=(10, 5))

        self.controller.calculate_saldi()
        self.refresh()

    def refresh(self):
        """Load the saldo from saldi.json and update the display."""
        # Clear previous rows if any
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Re-create header labels., 
        tk.Label(self.table_frame, text="Saldotype", bg="#009687", fg="white", font=('Helvetica', 15, 'bold'), anchor='w').grid(row=0, column=0, sticky='ew')
        tk.Label(self.table_frame, text="Til rådighed", bg="#009687", fg="white", font=('Helvetica', 15, 'bold'), anchor='w').grid(row=0, column=1, sticky='ew')

        try:
            with open(saldi_path, 'r') as file:
                saldi = json.load(file)
            for i, (saldo_type, amount) in enumerate(saldi.items()):
                # Skip certain types of saldo data
                if saldo_type == "flex_week":
                    continue

                row_color = "#F6F6F6" if i % 2 == 0 else "#E8E8E8"
                tipo = tk.Label(self.table_frame, text=saldo_type.capitalize(), bg=row_color, font=('Helvetica', 13), width=70, anchor='w')
                unit = 'dage' if saldo_type in ['omsorgsdage', 'seniordage'] else 'timer'
                formatted_amount = f"{self.controller.decimal_to_hours_minutes(amount)} {unit}" if saldo_type not in ['omsorgsdage', 'seniordage'] else f"{amount} {unit}"
                amount_label = tk.Label(self.table_frame, text=formatted_amount, bg=row_color, font=('Helvetica', 13), width=15, anchor='w', justify='right')
                tipo.grid(row=i+1, column=0, sticky='ew')
                amount_label.grid(row=i+1, column=1, sticky='ew')
        except FileNotFoundError as e:
            messagebox.showerror("Fejl", f"Saldi file not found: {str(e)}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Fejl", f"Error decoding JSON from saldi file: {str(e)}")






    def create_table_rows(self, parent):
        # Placeholder labels for table rows
        for i in range(5):
            row_color = "#F6F6F6" if i % 2 == 0 else "#E8E8E8"
            tipo = tk.Label(parent, text="", bg=row_color, font=('Helvetica', 13), width=70, anchor='w')
            amount = tk.Label(parent, text="", bg=row_color, font=('Helvetica', 13), width=15, anchor='w', justify='right')
            tipo.grid(row=i+1, column=0, sticky='ew')
            amount.grid(row=i+1, column=1, sticky='ew')
            self.rows.append((tipo, amount))