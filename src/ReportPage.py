import tkinter as tk


class ReportPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Eksportér rapport", font=('Helvetica', 16, 'bold')).pack(pady=(10, 5))
