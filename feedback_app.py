from tkinter import Tk, ttk
import tkinter as tk


class FeedbackApp(ttk.Frame):
    def __init__(self, master, feedback_helper):
        super().__init__()
        self.helper = feedback_helper
        self.master = master
        self.label=tk.Label(master)
        self.label.grid(row=0, column=0)
        self.label.configure(text=f"Feedback: {self.helper.mimm:.3f}")

        self.update()


    def update(self):
        self.helper.update()
        self.label.configure(text =f"Feedback: {self.helper.mimm:.3f}")
        self.master.after(50, self.update)
