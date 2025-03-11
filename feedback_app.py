import math
from tkinter import Tk, ttk
import tkinter as tk

class FeedbackApp(ttk.Frame):
    def __init__(self, window, feedback_helper):
        super().__init__()
        self.helper = feedback_helper
        self.window = window
        self.pack(fill="both", expand=True)

        # self.window.attributes('-fullscreen', True)
        self.window.geometry("1300x1300")
        self.window.title("Feedback application")

        self.canvas = tk.Canvas(window, width=1300, height=1300)

        self.mimm_height = 0.
        self.restmi_height = 700.

        self.mi_bar = self.canvas.create_rectangle(0, 0, 250, -self.mimm_height, fill='red')
        self.canvas.move(self.mi_bar, 700, 850)

        self.rest_bar = self.canvas.create_rectangle(0, 0, 250, -self.restmi_height, fill='blue')
        self.canvas.move(self.rest_bar, 350, 850)

        self.canvas.pack(fill="both", side="bottom", expand=True)

        self.task = "Break"
        self.symbol = self.canvas.create_text(650, 50, font=('Helvetica', '24', 'bold'), text="o")

        self.give_feedback = False
        self.count = 0 # debug
        self.continue_update = True

    def update(self):
        if self.give_feedback and self.helper.update() is not None:
            restmi, mimm = self.helper.update()

            self.restmi_height = 700 * restmi

            if self.task == "MI" and not self.helper.traditional:
                self.mimm_height = 700 * (1 - (1 / (1 + math.e ** (-8 * (mimm - .5)))))
            else:
                self.mimm_height = self.restmi_height

            print(f"\routput: restmi={restmi:.3f}, mimm={mimm:.3f}", end='')

            # self.mimm_height =+ self.count  # debug
            # self.count += 1 # debug

        elif self.helper.calibrating:
            self.mimm_height += 1.2
            self.restmi_height -= 1.2
        self.redraw()
        if self.continue_update:
            self.window.after(50, self.update)
        else:
            self.close()

    def redraw(self):
        self.canvas.delete(self.mi_bar)
        self.canvas.delete(self.rest_bar)
        if self.give_feedback or self.helper.calibrating:
            self.mi_bar = self.canvas.create_rectangle(0, 0, 250, -self.mimm_height, fill='red')
            self.canvas.move(self.mi_bar, 700, 850)

            self.rest_bar = self.canvas.create_rectangle(0, 0, 250, -self.restmi_height, fill='blue')
            self.canvas.move(self.rest_bar, 350, 850)


    def set_task(self, task):
        self.task = task
        if task == "MI":
            self.canvas.delete(self.symbol)
            self.symbol = self.canvas.create_text(650, 50, font=('Helvetica', '24', 'bold'), text="+")
        elif task == "Rest":
            self.canvas.delete(self.symbol)
            self.symbol = self.canvas.create_text(650, 50, font=('Helvetica', '24', 'bold'), text="-")
        elif task == "Break":
            self.canvas.delete(self.symbol)
            self.symbol = self.canvas.create_text(650, 50, font=('Helvetica', '24', 'bold'), text="o")
        else:
            raise ValueError(f"Unknown task: {task}")

    def close(self):
        self.window.quit()
        self.window.destroy()