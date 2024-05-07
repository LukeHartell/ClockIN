import tkinter as tk
from tkinter import messagebox
import json

class NewDayOffPage(tk.Frame):
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
