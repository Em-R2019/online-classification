import math
from random import uniform
from tkinter import ttk
import tkinter as tk

class FeedbackApp(ttk.Frame):
    def __init__(self, window, feedback_helper):
        super().__init__()
        self.helper = feedback_helper
        self.window = window
        self.pack(fill="both", expand=True)

        self.window.geometry("1300x1300")
        self.window.title("Feedback application")

        self.canvas = tk.Canvas(window, width=1300, height=1300)
        self.canvas.pack(fill="both", side="bottom", expand=True)

        self.mimm_height = 0
        self.restmi_height = 700

        self.mi_bar = None
        self.rest_bar = None

        self.task = "Break"
        self.symbol = "˄ = move or imagine \n˅ = relax \no = break"
        self.canvas_symbol = None
        self.give_feedback = False
        self.random_feedback = False

        # self.count = 0 # debug

        self.dummy_feedback = False
        self.dummy_delta_mimm = 1.3
        self.dummy_delta_restmi = -1.3

        self.write_symbol()
        self.draw_bars()

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
            self.mimm_height += self.dummy_delta_mimm
            self.restmi_height += self.dummy_delta_restmi

        elif self.dummy_feedback:
            self.generate_dummy_feedback()

        if self.restmi_height > 700:
            self.restmi_height = 700
        elif self.restmi_height < 0:
            self.restmi_height = 0

        if self.mimm_height > 700:
            self.mimm_height = 700
        elif self.mimm_height < 0:
            self.mimm_height = 0

        self.redraw()

        if self.continue_update:
            self.window.after(50, self.update)

    def redraw(self):
        self.draw_bars()
        self.write_symbol()

    def set_task(self, task):
        self.task = task
        if task == "MI":
            self.symbol = "˄"
        elif task == "Rest":
            self.symbol = "˅"
        elif task == "Break":
            self.symbol = "o"
        else:
            raise ValueError(f"Unknown task: {task}")

    def draw_bars(self):
        self.canvas.delete(self.mi_bar)
        self.canvas.delete(self.rest_bar)
        if self.give_feedback or self.helper.calibrating or self.dummy_feedback:
            self.mi_bar = self.canvas.create_rectangle(0, 0, 250, -self.mimm_height, fill='red')
            self.canvas.move(self.mi_bar, 720, 850)

            self.rest_bar = self.canvas.create_rectangle(0, 0, 250, -self.restmi_height, fill='blue')
            self.canvas.move(self.rest_bar, 330, 850)

    def write_symbol(self):
        self.canvas.delete(self.canvas_symbol)
        self.canvas_symbol = self.canvas.create_text(650, 500, font=('Helvetica', '60', 'bold'), text=self.symbol)

    def generate_dummy_feedback(self):
        if self.mimm_height >= 700:
            self.dummy_delta_mimm = - uniform(1, 5)
        elif self.mimm_height <= 0:
            self.dummy_delta_mimm = uniform(1, 5)
        if self.restmi_height >= 700:
            self.dummy_delta_restmi = - uniform(1, 5)
        elif self.restmi_height <= 0:
            self.dummy_delta_restmi = uniform(1, 5)

        self.mimm_height += self.dummy_delta_mimm
        self.restmi_height += self.dummy_delta_restmi