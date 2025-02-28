import threading
from tkinter import Tk, ttk
import tkinter as tk


class FeedbackApp(ttk.Frame):
    def __init__(self, window, feedback_helper):
        super().__init__()
        self.helper = feedback_helper
        self.window = window
        self.pack(fill="both", expand=True)

        # self.window.attributes('-fullscreen', True)
        self.window.geometry("800x800")
        self.window.title("Feedback application")

        self.canvas = tk.Canvas(window, width=800, height=800)

        self.mi_height = 100
        self.rest_height = 100

        self.mi_bar = self.canvas.create_rectangle(0, 0, 250, -self.mi_height, fill='red')
        self.canvas.move(self.mi_bar, 450, 750)

        self.rest_bar = self.canvas.create_rectangle(0, 0, 250, -self.rest_height, fill='blue')
        self.canvas.move(self.rest_bar, 150, 750)

        # self.canvas.create_text(100,10,font="Times 20 italic bold",
        #                         text="IMAGINE")

        self.canvas.pack(fill="both", side="bottom", expand=True)

        self.task = "Break"
        self.symbol = self.canvas.create_text(400, 10, font="Times 20 italic bold", text="o")

        self.give_feedback = False

        self.count = 0 # debug
        self.update()

    def update(self):
        self.helper.update()

        self.mi_height = 0
        self.rest_height = 0

        if self.helper.restmi > 0.5:
            self.mi_height = 700 * (self.helper.restmi - 0.5) * (self.helper.mimm + 0.1) / 1.1
            print(f"MI detected, output: mirest={self.helper.restmi:.3f}, mimm={self.helper.mimm:.3f}")
        else:
            self.rest_height = 700 * (1 - self.helper.restmi)
            print(f"No MI detected, output: mirest={self.helper.restmi:.3f}")

        self.mi_height =+ self.count  # debug
        self.count += 1 # debug

        self.redraw()
        self.master.after(50, self.update)

    def redraw(self):
        self.canvas.delete(self.mi_bar)
        self.canvas.delete(self.rest_bar)
        if self.give_feedback:
            self.mi_bar = self.canvas.create_rectangle(0, 0, 200, -self.mi_height, fill='red')
            self.canvas.move(self.mi_bar, 450, 750)

            self.rest_bar = self.canvas.create_rectangle(0, 0, 200, -self.rest_height, fill='blue')
            self.canvas.move(self.rest_bar, 150, 750)


    def set_task(self, task):
        self.task = task
        if task == "MI":
            self.canvas.delete(self.symbol)
            self.symbol = self.canvas.create_text(400, 10, font="Times 20 italic bold", text=">")
        elif task == "Rest":
            self.canvas.delete(self.symbol)
            self.symbol = self.canvas.create_text(400, 10, font="Times 20 italic bold", text="x")
        elif task == "Break":
            self.canvas.delete(self.symbol)
            self.symbol = self.canvas.create_text(400, 10, font="Times 20 italic bold", text="o")
        else:
            raise ValueError(f"Unknown task: {task}")


